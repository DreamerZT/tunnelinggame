"""
pygbag(웹) 실행용 엔트리포인트.

pygbag 템플릿은 APK 내부의 `assets/main.py`를 실행합니다.
이 파일이 없으면 브라우저에서 게임이 시작되지 않을 수 있습니다.
"""

import asyncio
import pygame

import tunneling_game


async def _run_game_async() -> None:
    game = tunneling_game.Game()
    while game.running:
        game.handle_input()
        game.update()
        game.draw()
        game.clock.tick(tunneling_game.FPS)
        # 브라우저 이벤트 루프에 양보
        await asyncio.sleep(0)
    pygame.quit()


def _start() -> None:
    """
    웹(브라우저) 환경에서는 이미 이벤트 루프가 돌고 있을 수 있어
    가능한 경우 task로 등록하고, 아니면 asyncio.run으로 실행합니다.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_run_game_async())
    except RuntimeError:
        asyncio.run(_run_game_async())


_start()


