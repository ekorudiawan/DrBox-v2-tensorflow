import pyrealsense2 as rs
import argparse
import imutils
import time
import cv2
import sys
import numpy as np
import glob
import os
import pickle

SHOW_DEPTH = False
CURRENT_PATH = os.getcwd()

def main():
    # Configure depth and color streams
    pipeline = rs.pipeline()
    config = rs.config()

    # Get device product line for setting a supporting resolution
    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()
    device_product_line = str(device.get_info(rs.camera_info.product_line))

    found_rgb = False
    for s in device.sensors:
        if s.get_info(rs.camera_info.name) == 'RGB Camera':
            found_rgb = True
            break
    if not found_rgb:
        print("The demo requires Depth camera with Color sensor")
        exit(0)

    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

    if device_product_line == 'L500':
        config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
    else:
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # Start streaming
    pipeline.start(config)

    # initialize the video stream and allow the camera sensor to warm up
    print("[INFO] starting video stream...")
    print("Current PATH : ", CURRENT_PATH)
    list_color_frame = []
    list_depth_frame = []
    try:
        while True:
            # Wait for a coherent pair of frames: depth and color
            frames = pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame:
                continue

            # Convert images to numpy arrays
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            # print("Distance at x=320, y=240 : ", depth_frame.get_distance(320,240))
            # print("Depth at x=320, y=240 : ", depth_image[240, 320])

            # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
            depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
            depth_colormap_dim = depth_colormap.shape
            color_colormap_dim = color_image.shape           
            
            if depth_colormap_dim != color_colormap_dim:
                resized_color_image = cv2.resize(color_image, dsize=(depth_colormap_dim[1], depth_colormap_dim[0]), interpolation=cv2.INTER_AREA)
            else:
                resized_color_image = color_image

            # original image
            original_image = resized_color_image.copy()

            if SHOW_DEPTH:
                # If depth and color resolutions are different, resize color image to match depth image for display
                if depth_colormap_dim != color_colormap_dim:
                    images = np.hstack((resized_color_image, depth_colormap))
                else:
                    images = np.hstack((color_image, depth_colormap))
            else:
                images = resized_color_image
            
            cv2.namedWindow("RealSense Viewer", cv2.WINDOW_AUTOSIZE)
            cv2.imshow("RealSense Viewer", images)
            
            key = cv2.waitKey(1) & 0xFF
            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                if(len(list_color_frame)>0):
                    with open(CURRENT_PATH + '/d455_data/list_color_frame.pickle', 'wb') as f:
                        pickle.dump(list_color_frame, f)
                        print("Save list_color_frame.pickle ")
                    with open(CURRENT_PATH + '/d455_data/list_depth_frame.pickle', 'wb') as f:
                        pickle.dump(list_depth_frame, f)
                        print("Save list_depth_frame.pickle ")
                break
            elif key == ord('s'):
                print("Add image to list")
                list_color_frame.append(color_image)
                list_depth_frame.append(depth_image)
    
    finally:
        # Stop streaming
        pipeline.stop()
        # do a bit of cleanup
        cv2.destroyAllWindows()
        
if __name__ == "__main__":
    main()

