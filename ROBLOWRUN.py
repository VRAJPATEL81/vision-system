from roboflow import Roboflow

rf = Roboflow(api_key="VK9dNheJEhVc82ujhDKY")

project = rf.workspace("dent-detection-tsf5p").project("dent_detection-u6d2r")

model = project.version(3).model

result = model.predict("D:/ATOMONE/YOLOv8_dataset/images/rms10.jpeg", confidence=40)

result.save("result.jpeg")

print(result.json())
