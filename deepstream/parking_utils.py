import math
import time
import json


def calculate_center_distance(quad, rect):
    # 计算四边形的中心点
    quad_center_x = sum([point[0] for point in quad]) / 4
    quad_center_y = sum([point[1] for point in quad]) / 4
    
    # 计算矩形的中心点
    rect_center_x = (rect[0] + rect[2]) / 2
    rect_center_y = (rect[1] + rect[3]) / 2
    
    # 计算欧几里得距离
    distance = math.sqrt((quad_center_x - rect_center_x)**2 + (quad_center_y - rect_center_y)**2)
    return distance


def calculate_rectangle_diameter(rect):
    # 获取矩形的左下角和右上角坐标
    x_min, y_min, x_max, y_max = rect
    
    # 计算对角线（矩形的直径）
    diameter = math.sqrt((x_max - x_min)**2 + (y_max - y_min)**2)
    return diameter


def in_event(car_data, parking_id, frame_num):
    header = {"Content-Type":"application/json"}
    keys = {"event_id", "envet_type", "in_time", "out_time", "parking_no",
            "plate_no", "car_type", "plate_color", "car_color", "score"}
    response = {}
    for key in keys:
        response[key] = ""
    response["event_id"] = str(int(time.time()*1000))
    response["envet_type"] = "1"
    response["in_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    response["parking_no"] = parking_id
    response["car_type"] = car_data["class"]
    response["plate_no"] = car_data["plate_num"]
    response["score"] = car_data["rec_score"]
    response["frame_num"] = frame_num
    return response


def out_event(car_data, parking_id, frame_num):
    header = {"Content-Type":"application/json"}
    keys = {"event_id", "envet_type", "in_time", "out_time", "parking_no",
            "plate_no", "car_type", "plate_color", "car_color", "score"}
    response = {}
    for key in keys:
        response[key] = ""
    response["event_id"] = str(int(time.time()*1000))
    response["envet_type"] = "2"
    response["out_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    response["parking_no"] = parking_id
    response["car_type"] = car_data["class"]
    response["plate_no"] = car_data["plate_num"]
    response["score"] = car_data["rec_score"]
    response["frame_num"] = frame_num
    return response


def demo_event(frame, data, parking, json_path):
        car_bbox = data["bbox"]
        for parking_id, parking_boxes in parking:
            dis = calculate_center_distance(parking_boxes, car_bbox)
            threshold = calculate_rectangle_diameter(car_bbox) / 3
            if data["rec_score"] is None:
                continue
            if data["rec_score"] < 0.8:
                continue
            if data["parking"] == "out": 
                if dis < threshold:      # 说明车进停车位
                    response = in_event(data, parking_id, frame)
                    with open(json_path, "a", encoding="utf-8") as f_out:
                        f_out.write(json.dumps(response, ensure_ascii=False) + "\n")
                    data["parking"] = parking_id
            elif data["parking"] == parking_id:
                if dis > threshold:      # 说明车出停车位
                    response = out_event(data, parking_id, frame)
                    with open(json_path, "a", encoding="utf-8") as f_out:
                        f_out.write(json.dumps(response, ensure_ascii=False) + "\n")
                    data["parking"] = "out"