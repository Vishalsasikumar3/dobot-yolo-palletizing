import cv2
import time
from ultralytics import YOLO
from pydobot.dobot import MODE_PTP
import pydobot

device = pydobot.Dobot(port="/dev/ttyACM0")
device.speed(100, 100)
device.home()

# replace the 5 with actual camera index, get_camera_index.py
cap = cv2.VideoCapture(2)
if not cap.isOpened():
    raise RuntimeError("Cannot open camera")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

model = YOLO("yolov8s.pt")

# touch up the following coordinates
home_coordinates = [239.999, 0.0, 150.0, -8.881]
intermediate_coordinates = [193.526, 22.005, 35.189, 6.487]
pickup_coordinates = [306.420, -82.706, -55.166, -15.104]
palleteA_coordinates = [210.180, -233.553, 24.075, -46.766]
palleteB_coordinates = [303.931, 220.869, 26.487, 36.006]

def is_home():
    """Check if robot is at home position"""
    pose = device.get_pose()
    
    # Try different ways to extract position based on pydobot version
    try:
        current_pose = (pose.position.x, pose.position.y, pose.position.z, pose.position.r)
    except AttributeError:
        try:
            current_pose = (pose.x, pose.y, pose.z, pose.r)
        except AttributeError:
            # If it's already a tuple/list
            current_pose = tuple(pose[:4]) if hasattr(pose, '__iter__') else pose
    
    # Use actual home coordinates for comparison
    home_pose = tuple(home_coordinates)
    
    # Check only X, Y, Z position (ignore rotation)
    position_tol = 10  # 10mm tolerance for position
    is_at_home = all(abs(current_pose[i] - home_pose[i]) < position_tol for i in range(3))
    
    print(f"Current pose: {current_pose}, At home: {is_at_home}")
    return is_at_home

def reopen_camera():
    """Safely reopen the camera"""
    global cap
    if cap is not None and cap.isOpened():
        cap.release()
    
    time.sleep(1.5)  # Longer wait for camera release
    
    for attempt in range(3):  # Try 3 times
        cap = cv2.VideoCapture(2)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            print("Camera reopened successfully")
            return
        time.sleep(1)
    
    raise RuntimeError("Cannot reopen camera after 3 attempts")

try:
    print("Starting object detection and palletization...")
    print("Press 'q' to quit")
    
    # Create window for display
    cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)
    
    while True:
        # Check if at home position, if not wait
        if not is_home():
            print("Waiting for robot to return home...")
            time.sleep(1)
            continue

        ret, frame = cap.read()
        if not ret:
            print("Camera error, trying to reopen...")
            reopen_camera()
            continue

        # Run YOLO detection
        results = model(frame, verbose=False)
        r = results[0]

        # Draw bounding boxes on frame
        annotated_frame = r.plot()  # This draws boxes and labels
        
        detected_class = None
        detected_label = "None"
        
        if r.boxes is not None and len(r.boxes) > 0:
            cls = r.boxes.cls.cpu().numpy().astype(int)
            names = r.names

            # Loop over detections
            for k in cls:
                label = names[k].lower()
                print(f"Detected: {label}")

                if label in ["car", "truck", "bus", "motorbike", "bicycle"]:
                    detected_class = "vehicle"
                    detected_label = label
                    break
                elif label in ["apple", "banana", "sandwich", "pizza", "cake"]:
                    detected_class = "food"
                    detected_label = label
                    break

        # Add text overlay showing detection status
        status_text = f"Status: {detected_class if detected_class else 'Waiting...'}"
        label_text = f"Object: {detected_label}"
        
        cv2.putText(annotated_frame, status_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(annotated_frame, label_text, (10, 70), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display the frame
        cv2.imshow('Camera Feed', annotated_frame)
        
        # Check for 'q' key to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Quit key pressed")
            break

        if detected_class == "food":
            print("Food detected → waiting 10 seconds before moving to Pallet A")
            time.sleep(0.5)  # Wait 10 seconds after detection
            cap.release()
            cv2.destroyAllWindows()
            
            device.move_to(mode=int(MODE_PTP.MOVJ_XYZ),
                           x=pickup_coordinates[0], y=pickup_coordinates[1],
                           z=pickup_coordinates[2], r=pickup_coordinates[3])
            time.sleep(0.3)
            device.suck(True)
            time.sleep(0.5)
            
            device.move_to(mode=int(MODE_PTP.MOVJ_XYZ),
                           x=intermediate_coordinates[0], y=intermediate_coordinates[1],
                           z=intermediate_coordinates[2], r=intermediate_coordinates[3])
            
            device.move_to(mode=int(MODE_PTP.MOVJ_XYZ),
                           x=palleteA_coordinates[0], y=palleteA_coordinates[1],
                           z=palleteA_coordinates[2], r=palleteA_coordinates[3])
            time.sleep(0.3)
            device.suck(False)
            time.sleep(0.5)
            
            device.home()
            time.sleep(2)  # Wait for object to be removed
            reopen_camera()
            cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)

        elif detected_class == "vehicle":
            print("Vehicle detected → waiting 10 seconds before moving to Pallet B")
            time.sleep(10)  # Wait 10 seconds after detection
            cap.release()
            cv2.destroyAllWindows()
            
            device.move_to(mode=int(MODE_PTP.MOVJ_XYZ),
                           x=pickup_coordinates[0], y=pickup_coordinates[1],
                           z=pickup_coordinates[2], r=pickup_coordinates[3])
            time.sleep(0.3)
            device.suck(True)
            time.sleep(0.5)
            
            device.move_to(mode=int(MODE_PTP.MOVJ_XYZ),
                           x=intermediate_coordinates[0], y=intermediate_coordinates[1],
                           z=intermediate_coordinates[2], r=intermediate_coordinates[3])
            
            device.move_to(mode=int(MODE_PTP.MOVJ_XYZ),
                           x=palleteB_coordinates[0], y=palleteB_coordinates[1],
                           z=palleteB_coordinates[2], r=palleteB_coordinates[3])
            time.sleep(0.3)
            device.suck(False)
            time.sleep(0.5)
            
            device.home()
            time.sleep(2)  # Wait for object to be removed
            reopen_camera()
            cv2.namedWindow('Camera Feed', cv2.WINDOW_NORMAL)
        
        else:
            # No object detected, continue
            time.sleep(0.05)

except KeyboardInterrupt:
    print("\nStopping program...")
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()
finally:
    cv2.destroyAllWindows()
    if cap is not None:
        cap.release()
    device.close()
    print("Cleanup complete")