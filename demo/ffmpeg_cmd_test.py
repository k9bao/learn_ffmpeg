import unittest
import os
from . import VideoProp


class TestIllegal(unittest.TestCase):
    def __init__(self):
        self.src_file = "big_buck_bunny.mp4"
        self.first_file = "1.mp4"
        self.second_file = "2.mp4"
        self.third_file = "3.mp4"

    def test_cut(self):
        os.system(f"ffmpeg -y -ss 0 -to 8 -i {self.src_file} -codec copy {self.first_file}")
        os.system(f"ffmpeg -y -ss 0 -to 8 -i {self.src_file} -codec copy {self.second_file}")
        os.system(f"ffmpeg -y -ss 0 -to 8 -i {self.src_file} -codec copy {self.third_file}")


if __name__ == "__main__":
    unittest.main()

# 验证下载文件和获取信息，那个耗时长？
# ffmpeg -i "http://9.21.8.134/defaultts.tc.qq.com/gBuKd2HfFSancnmpwle2H6XyuJ7Ct-ArFH3MAnoSfdT2oIebEHq3wW6uqYWYANLpzS-eDOjp-/Eif3pHb9cWickTgnMWZPDBWo9Czovu_eBqmP2wBpDwKO2HM4ESC74zx3rpCfUREgUYuqJhFSoOR8A/i0036jbwmu9.321004.ts.m3u8?ver=4" test.mp4
