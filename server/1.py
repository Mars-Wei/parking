from car_detection import *
from draw import *
from utils import *
from demo_utils import *
import cv2


def parking_detection(video_path, parking, output_video_path):
    # 原始视频
    data = {}
    cap = cv2.VideoCapture(video_path)
    frame_num = -1
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    car_detecter = carDetection("./models/yolo11/yolo11l.pt")


    # 输出视频
    fourcc = cv2.VideoWriter_fourcc(*'h264')  # 使用 'h264' 编码器
    fps = cap.get(cv2.CAP_PROP_FPS)  # 获取原始视频的帧率
    frame_size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    out = cv2.VideoWriter(output_video_path, fourcc, fps, frame_size)


    if not cap.isOpened():
        print("无法打开视频")
        return

    while True:
        # 逐帧读取视频流
        ret, frame = cap.read()
        
        if not ret:
            break
        # 开始车辆检测
        frame_num += 1
        # if frame_num % 10 != 0:
        #     continue
        # if frame_num > 60:
        #     break
        cars = car_detecter(frame)
        t1 = time.time()
        for car_id in cars.keys():
            if car_id not in data:
                data[car_id] = {"class":None, "plate_num":None, "rec_score":None, "bbox":None, "det_score":None, "parking":"out"}
            car_bbox = cars[car_id]["bbox"]
            data[car_id]["class"] = cars[car_id]["class"]
            data[car_id]["bbox"] = car_bbox
            data[car_id]["det_score"] = cars[car_id]["det_score"]

             # 对于小于150*150的车 不做车牌检测
            if car_bbox[2] - car_bbox[0] < 150:
                continue
            if car_bbox[3] - car_bbox[1] < 150:
                continue

            # 当前车牌置信度大于0.99 也可以不做车牌检测
            if data[car_id]["rec_score"] is not None and data[car_id]["rec_score"] > 0.99:
                continue

            cropped_image = frame[car_bbox[1]:car_bbox[3], car_bbox[0]:car_bbox[2]]
            plate_res = car_plate_num(plate_url, cropped_image)
            for j in range(len(plate_res)):
                # print(dt_boxes[j].tolist(), rec_res[j])
                plate_num = plate_res[j]["plate_number"]
                rec_socre = round(plate_res[j]["rec_socre"], 3)
                # print(plate_num, rec_socre)
                if data[car_id]["rec_score"] is None or data[car_id]["rec_score"]<rec_socre:
                    data[car_id]["plate_num"] = plate_num
                    data[car_id]["rec_score"] = rec_socre
        demo_event(frame=frame_num, data=data, parking=parking, json_path=output_video_path.replace(".mp4", ".jsonl"))
        t2 = time.time()
        res = draw_fun(image=frame, data=filter_visible_data(data=data, cars=cars, threshold=0.2))
        res = draw_parking_space(image=res, parking=parking)
        t3 = time.time()
        cv2.imshow("demo", res)
        print(frame_num, "车牌检测耗时", round(t2-t1, 3), "可视化耗时", round(t3-t2, 3))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        out.write(res)
        # breakpoint()
    cap.release()


# 设置 CUDA_VISIBLE_DEVICES 环境变量
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
plate_url = "http://127.0.0.1:9100/analysis"


if __name__ == "__main__":
    # with open("demo.json", "r", encoding="utf-8") as f:
    #     data = json.loads(f.read())
    #     print(data)
    #     cnt = -1
    #     for video in data:
    #         cnt += 1
    #         print(cnt, video)
    #         if cnt != 2 :
    #             continue
    #         parking = data[video]
    #         video = "./videos/{}.mp4".format(video)
    #         print(video, parking)
    #         parking_detection(video_path=video, parking=parking, output_video_path="out/demo_{}.mp4".format(cnt))
    cap = cv2.VideoCapture("out/demo_2.mp4")
    if not cap.isOpened():
        print("无法打开视频")
        breakpoint()
    cap.set(cv2.CAP_PROP_POS_FRAMES, 970)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # 逐帧读取视频流
        cv2.imshow("demo", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
        cv2.imwrite("aaa.jpg", frame)
        break
    cap.release()
