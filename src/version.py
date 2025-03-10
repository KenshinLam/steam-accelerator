#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
版本信息模块
"""

__version__ = '1.0.1'
__author__ = 'Steam加速器团队'
__release_date__ = '2025-03-11'

# 版本历史
VERSION_HISTORY = {
    '1.0.1': {
        'date': '2025-03-11',
        'description': '版本更新',
        'changes': [
            '修复已知问题',
            '优化用户体验'
        ]
    },
    '1.0.0': {
        'date': '2025-03-11',
        'description': '初始版本发布',
        'changes': [
            '支持DOTA2和CS2游戏加速',
            '支持国服、香港和东南亚区服',
            '智能节点选择功能',
            '实时延迟监控'
        ]
    }
}


def get_version():
    """获取当前版本号"""
    return __version__


def get_version_info():
    """获取当前版本详细信息"""
    return VERSION_HISTORY.get(__version__, {})