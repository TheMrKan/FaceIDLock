import cv2


def get_available_captures() -> list:
    index = 0
    arr = []
    while index < 50:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            arr.append(index)

        index += 1
    return arr


if __name__ == "__main__":
    print(get_available_captures())