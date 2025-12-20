#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Poker HUD 3.01 메인 실행 파일
모듈화된 포커 HUD 시스템의 진입점
"""

# === Standard Library Imports ===
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# === Local Imports ===
from poker_hud_manager import main

if __name__ == "__main__":
    main()