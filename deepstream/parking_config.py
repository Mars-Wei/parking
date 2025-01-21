import json

def load_parking_config(config_file):
    """
    加载停车配置 JSON 文件.

    Args:
        config_file (str): JSON 配置文件路径.

    Returns:
        dict: 配置字典, 如果加载失败返回 None.
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {config_file}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in: {config_file}")
        return None

def process_parking_config(config):
    """
    处理加载的停车配置字典，打印相关信息.

    Args:
       config (dict): 配置字典.
    """
    if not config:
        return

    print("Network Configuration:")
    print(f"  Push URL: {config['network']['push_url']}")
    print(f"  Event URL: {config['network']['event_url']}")

    print("\nStream Configurations:")
    for stream_id, stream_data in config['streams'].items():
        print(f"\n  Stream ID: {stream_id}")
        print(f"    Parking Nos: {stream_data['parking_no']}")
        print("    Parking Rectangles:")
        for i, rect in enumerate(stream_data['parking_recs']):
            print(f"      Rectangle {i + 1}: {rect}")


if __name__ == '__main__':
    config_file = "/Users/yanyu/work/ai_box_stuff/parking/deepstream/parking_config.json"  # 你的实际文件路径
    parking_config = load_parking_config(config_file)
    process_parking_config(parking_config)