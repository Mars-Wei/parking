import json
import math
import time
import cv2
import requests

class ParkingDetector:
    def __init__(self, parking_config, json_path="/tmp/parking_demo.log", score_threshold=0.8):
        self.parking_config = parking_config
        self.data = {}
        self.json_path = json_path
        self.score_threshold = score_threshold

    @staticmethod
    def calculate_center_distance(quad_points, rect_coords):
        """
        计算四边形和矩形中心点之间的欧几里得距离。

        :param quad_points: 四边形的四个顶点坐标
        :param rect_coords: 矩形的左下角和右上角坐标
        :return: 欧几里得距离
        """
        quad_center_x = sum([point[0] for point in quad_points]) / 4
        quad_center_y = sum([point[1] for point in quad_points]) / 4

        rect_center_x = (rect_coords[0] + rect_coords[2]) / 2
        rect_center_y = (rect_coords[1] + rect_coords[3]) / 2

        distance = math.sqrt((quad_center_x - rect_center_x) ** 2 + (quad_center_y - rect_center_y) ** 2)
        return distance

    @staticmethod
    def calculate_rectangle_diameter(rect_coords):
        """
        计算矩形的对角线长度（即矩形的直径）。

        :param rect_coords: 矩形的左下角和右上角坐标
        :return: 矩形的直径
        """
        x_min, y_min, x_max, y_max = rect_coords
        diameter = math.sqrt((x_max - x_min) ** 2 + (y_max - y_min) ** 2)
        return diameter

    @staticmethod
    def create_event(car_data, parking_id, frame_num, event_type, event_time_key, event_time):
        """
        构造停车事件消息。

        :param car_data: 包含车辆信息的字典
        :param parking_id: 停车场编号
        :param frame_num: 帧号
        :param event_type: 事件类型（1: 入库, 2: 出库）
        :param event_time_key: 事件时间的键名（"in_time" 或 "out_time"）
        :param event_time: 事件时间
        :return: 事件响应字典
        """
        header = {"Content-Type": "application/json"}
        keys = ["event_id", "event_type", "in_time", "out_time", "parking_no",
                "plate_no", "car_type", "plate_color", "car_color", "score", "frame_num"]
        response = {key: "" for key in keys}

        response["event_id"] = str(int(time.time() * 1000))
        response["event_type"] = event_type
        response[event_time_key] = event_time
        response["parking_no"] = parking_id
        response["plate_no"] = car_data["plate_num"]
        response["car_type"] = car_data["class"]
        response["score"] = car_data["rec_score"]
        response["frame_num"] = frame_num
        return response

    def log_event(self, event):
        """
        记录事件到文件。

        :param event: 事件字典
        """
        with open(self.json_path, "a", encoding="utf-8") as f_out:
            f_out.write(json.dumps(event, ensure_ascii=False) + "\n")


    def trigger_external_event(self,event):
        """
        调用外部接口触发事件。

        :param event: 事件字典
        """
        # 这里可以添加调用外部接口的逻辑
        print(f"Triggering external event: {event}")
        url = self.parking_config["network"]["event_url"]
        if url:
            try:
                headers = {'Content-type': 'application/json'}
                response = requests.post(url, json=event, headers=headers)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                print(f"Event pushed successfully to {url}: {response.text}")
            except requests.exceptions.RequestException as e:
                    print(f"Failed to push event to {url}: {e}")
        else:
            print("No push_url configured. Event not pushed.")

    def handle_parking_event(self, car_data, parking_id, frame_num, event_type, event_time):
        """
        处理停车事件，记录日志并触发外部事件。

        :param car_data: 包含车辆信息的字典
        :param parking_id: 停车场编号
        :param frame_num: 帧号
        :param event_type: 事件类型（1: 入库, 2: 出库）
        :param event_time: 事件时间
        """
        event = self.create_event(car_data, parking_id, frame_num, event_type, "in_time" if event_type == 1 else "out_time", event_time)
        self.log_event(event)
        self.trigger_external_event(event)

    def process_frame(self, source_id,frame, car):
        """
        处理单帧视频，进行车辆检测和车牌识别。
        :param frame: 当前帧号
        :param car: 检测到的车辆信息
        """
        # for car_id in cars.keys():
        # car = cars[car_id]
        car_bbox = car["bbox"]
        # 小于检测准确度阈值，跳过
        if car["rec_score"] < self.score_threshold:
            return
        # 对于小于150*150的车，跳过
        if car_bbox[2] - car_bbox[0] < 150 or car_bbox[3] - car_bbox[1] < 150:
            return
        self.check_parking_intention(frame, source_id,car)

    def check_parking_intention(self, frame, source_id, car):
        """
        车辆停车意图检测，同时记录车辆进出停车位的事件。
        :param frame: 当前帧号
        :param car: 当前识别的车辆信息
        """
        car_id = car["car_id"]
        if car_id not in self.data:
            self.data[car_id] = {"class": car["class"], "plate_num": car["plate_num"], "rec_score": car["rec_score"], "bbox": car["bbox"], "det_score": car["det_score"], "parking": "out"}

        car_bbox = car["bbox"]
        car_data = self.data[car_id]
        parking_info = self.parking_config['streams'][source_id]
        for parking_id, parking_boxes in zip(parking_info['parking_ids'],parking_info['parking_rects']):
            dis = self.calculate_center_distance(parking_boxes, car_bbox)
            threshold = self.calculate_rectangle_diameter(car_bbox) / 3

            if car_data["parking"] == "out":
                if dis < threshold:  # 说明车进停车位
                    event_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                    self.handle_parking_event(car_data, parking_id, frame, 1, event_time)
                    car_data["parking"] = parking_id
            elif car_data["parking"] == parking_id:
                if dis > threshold:  # 说明车出停车位
                    event_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                    self.handle_parking_event(car_data, parking_id, frame, 2, event_time)
                    car_data["parking"] = "out"

def detect_cars(frame):
    """
    假设的车辆检测函数，返回检测到的车辆信息。
    这里需要根据实际情况实现车辆检测逻辑。
    """
    # 示例返回值
    return {
        "car_1": {
            "car_id": "car_1",
            "class": "sedan",
            "plate_num": "ABC123",
            "rec_score": 0.9,
            "bbox": [100, 100, 300, 300],
            "det_score": 0.95
        }
    }

def test(video_path, parking, output_video_path):
    """
    主函数，处理视频文件并记录车辆进出停车位的事件。

    :param video_path: 输入视频文件路径
    :param parking: 停车位信息
    :param output_video_path: 输出视频文件路径
    """
    json_path = output_video_path.replace(".mp4", ".jsonl")
    pd = ParkingDetector(parking, json_path)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("无法打开视频")
        return

    frame_num = 0

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            cars = detect_cars(frame)
            pd.process_frame(frame_num, cars)
            frame_num += 1

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

from parking_config import load_parking_config
def test2():
    pd = ParkingDetector(load_parking_config())
    left = 1899.132568359375
    top = 1033.59619140625
    width = 90.72988891601562
    height = 33.31583023071289
    rect = [
                    # left bottom
                    left,
                    top + height,
                    # right top
                    left +width, 
                    top
                ]
    pd.process_frame("/live/v01", 10, {
        "car_id": "car_1",
        "class": "sedan",
        "plate_num": "津NLU035",
        "rec_score": 0.9,
        "bbox": rect,
        # "bbox": [100, 100, 300, 300],
        "det_score": 0.95
    })

if __name__ == "__main__":
    # video_path = "path/to/input/video.mp4"
    # parking = {
    #     "parking1": [[150, 150, 250, 250]],
    #     "parking2": [[350, 350, 450, 450]]
    # }
    # output_video_path = "path/to/output/video.mp4"
    # test(video_path, parking, output_video_path)
    test2()