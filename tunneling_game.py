import pygame
import sys
import random
import json
import os
from datetime import timedelta

# 한글 폰트(웹/배포 포함) 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KOREAN_FONT_PATH = os.path.join(BASE_DIR, "fonts", "NotoSansKR.ttf")
_FONT_CACHE = {}

# 실행 환경 플래그
# - 웹(브라우저) 빌드: pygbag/emscripten 환경에서 sys.platform == "emscripten"
IS_WEB_BUILD = (sys.platform == "emscripten")
# - 개발용 기능(예: 테스트 모드)은 기본 OFF. 필요할 때만 환경변수로 켠다.
#   Windows(PowerShell):  $env:TUNNELINGGAME_DEVTOOLS="1"
#   Windows(CMD):         set TUNNELINGGAME_DEVTOOLS=1
DEV_TOOLS_ENABLED = os.getenv("TUNNELINGGAME_DEVTOOLS", "").strip().lower() in ("1", "true", "yes", "y")

# Pygame 초기화
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    # 웹 빌드/일부 환경에서는 오디오 초기화가 실패할 수 있음 (게임 진행에는 영향 없음)
    pass


def get_game_font(size: int) -> pygame.font.Font:
    """게임 공통 폰트 로더 (한글 지원)."""
    key = ("kr", size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    # 1) 프로젝트에 포함된 오픈소스 한글 폰트 우선
    if os.path.exists(KOREAN_FONT_PATH):
        font = pygame.font.Font(KOREAN_FONT_PATH, size)
    else:
        # 2) 로컬 실행 시 시스템 폰트(맑은 고딕 등) 시도
        try:
            font = pygame.font.SysFont("malgungothic", size)
        except Exception:
            # 3) 최후의 fallback (영문 위주)
            font = pygame.font.Font(None, size)

    _FONT_CACHE[key] = font
    return font

# 게임 설정
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
UI_HEIGHT = 95
GAME_FIELD_Y = UI_HEIGHT
FLOOR_HEIGHT = 80
PLAYER_SIZE = 60
MONSTER_SIZE = 50
TOTAL_FLOORS = 51  # 지상 1층 + 지하 50층
FPS = 60

# 현대적인 색상 팔레트
BG_DARK = (15, 23, 42)
BG_DARKER = (2, 6, 23)
CARD_BG = (30, 41, 59)
CARD_BORDER = (51, 65, 85)

TEXT_PRIMARY = (248, 250, 252)
TEXT_SECONDARY = (203, 213, 225)
TEXT_MUTED = (148, 163, 184)

PRIMARY = (59, 130, 246)
PRIMARY_HOVER = (96, 165, 250)
SUCCESS = (34, 197, 94)
WARNING = (234, 179, 8)
DANGER = (239, 68, 68)
INFO = (168, 85, 247)

PLAYER_COLOR = (96, 165, 250)
GROUND_SURFACE = (22, 163, 74)
GROUND_SURFACE_DARK = (21, 128, 61)
GROUND_UNDERGROUND = (120, 53, 15)
GROUND_UNDERGROUND_DARK = (87, 38, 10)
HOLE_COLOR = (23, 23, 23)

# 몬스터 색상
SKELETON_COLOR = (226, 232, 240)
BAT_COLOR = (192, 132, 252)
ZOMBIE_COLOR = (74, 222, 128)
DRACULA_COLOR = (220, 38, 38)
ORC_COLOR = (22, 101, 52)

# 기믹 색상
GIMMICK_TELEPORT = (250, 204, 21)  # 노란색 - 순간이동
GIMMICK_INVISIBLE = (251, 146, 60)  # 주황색 - 투명화
GIMMICK_SLOW = (168, 85, 247)  # 보라색 - 감속
GIMMICK_SPEED = (236, 72, 153)  # 분홍색 - 가속
GIMMICK_STUN = (23, 23, 23)  # 검정색 - 마비

GLOW_COLOR = (96, 165, 250, 100)
SHADOW_COLOR = (0, 0, 0, 80)

def draw_rounded_rect(surface, color, rect, radius=10, border_width=0, border_color=None):
    """둥근 모서리 사각형"""
    x, y, w, h = rect
    pygame.draw.rect(surface, color, (x + radius, y, w - 2*radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2*radius))
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)
    
    if border_width > 0 and border_color:
        pygame.draw.rect(surface, border_color, (x + radius, y, w - 2*radius, border_width))
        pygame.draw.rect(surface, border_color, (x + radius, y + h - border_width, w - 2*radius, border_width))
        pygame.draw.rect(surface, border_color, (x, y + radius, border_width, h - 2*radius))
        pygame.draw.rect(surface, border_color, (x + w - border_width, y + radius, border_width, h - 2*radius))

class Gimmick:
    """기믹 클래스"""
    def __init__(self, floor_num, gimmick_type, x_pos):
        self.floor = floor_num
        self.type = gimmick_type  # 'teleport', 'invisible', 'slow', 'speed', 'stun'
        self.x = x_pos
        self.width = 80
        self.is_active = True
        self.glow_pulse = 0
        
    def get_color(self):
        """기믹 타입별 색상"""
        colors = {
            'teleport': GIMMICK_TELEPORT,
            'invisible': GIMMICK_INVISIBLE,
            'slow': GIMMICK_SLOW,
            'speed': GIMMICK_SPEED,
            'stun': GIMMICK_STUN
        }
        return colors.get(self.type, (255, 255, 255))
    
    def draw(self, screen, camera_y):
        """기믹 그리기"""
        if not self.is_active:
            return
            
        y_pos = GAME_FIELD_Y + self.floor * FLOOR_HEIGHT - camera_y
        
        # 화면에 보이는지 확인
        if not (GAME_FIELD_Y - FLOOR_HEIGHT <= y_pos <= SCREEN_HEIGHT):
            return
        
        # 글로우 펄스 애니메이션
        self.glow_pulse = (self.glow_pulse + 0.1) % (3.14 * 2)
        pulse_size = int(20 + 10 * abs(pygame.math.Vector2(1, 0).rotate(self.glow_pulse * 50).x))
        
        # 글로우 효과
        glow_surf = pygame.Surface((self.width + pulse_size, FLOOR_HEIGHT + pulse_size), pygame.SRCALPHA)
        color = self.get_color()
        pygame.draw.rect(glow_surf, color + (50,), (0, 0, self.width + pulse_size, FLOOR_HEIGHT + pulse_size))
        screen.blit(glow_surf, (self.x - pulse_size // 2, y_pos - pulse_size // 2))
        
        # 기믹 영역 표시
        gimmick_rect = pygame.Rect(self.x, y_pos, self.width, FLOOR_HEIGHT)
        pygame.draw.rect(screen, color + (100,), gimmick_rect)
        draw_rounded_rect(screen, color + (150,), gimmick_rect, 5, 2, color)

class Player:
    """플레이어 클래스"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.base_speed = 5
        self.speed = 5
        self.current_floor = 0
        self.is_digging = False
        self.dig_timer = 0
        self.dig_duration = 60
        
        # 상태 효과
        self.is_invisible = False
        self.invisible_end_floor = 0
        self.is_stunned = False
        self.stun_timer = 0
        self.speed_effect_timer = 0
        self.speed_multiplier = 1.0
        
    def move(self, dx, floors):
        """좌우 이동"""
        if self.is_stunned:
            return
        
        actual_speed = self.base_speed * self.speed_multiplier
        new_x = self.x + dx * actual_speed
        if 50 <= new_x <= SCREEN_WIDTH - self.width - 50:
            self.x = new_x
    
    def move_down(self, floors):
        """아래층으로 이동"""
        if self.is_stunned:
            return False
        
        if self.current_floor < TOTAL_FLOORS - 1:
            current_holes = floors[self.current_floor]['holes']
            for hole_start, hole_end in current_holes:
                if hole_start <= self.x + self.width // 2 <= hole_end:
                    self.current_floor += 1
                    # 투명화 효과 체크
                    if self.is_invisible and self.current_floor >= self.invisible_end_floor:
                        self.is_invisible = False
                    return True
        return False
    
    def jump(self):
        """위층으로 점프"""
        if self.is_stunned:
            return False
        
        if self.current_floor > 0:
            self.current_floor -= 1
            return True
        return False
    
    def start_digging(self, floors, gimmicks):
        """땅굴 파기"""
        if self.is_stunned:
            return
        
        if not self.is_digging:
            current_holes = floors[self.current_floor]['holes']
            player_center = self.x + self.width // 2
            
            # 기믹 체크 (구멍 유무와 관계없이 먼저 체크)
            for gimmick in gimmicks:
                if gimmick.floor == self.current_floor and gimmick.is_active:
                    if gimmick.x <= player_center <= gimmick.x + gimmick.width:
                        self.activate_gimmick(gimmick)
                        # 기믹을 획득했으므로 파기 시작
                        self.is_digging = True
                        self.dig_timer = self.dig_duration
                        return
            
            # 기믹이 없는 경우, 일반 파기 체크
            already_dug = False
            for hole_start, hole_end in current_holes:
                if hole_start <= player_center <= hole_end:
                    already_dug = True
                    break
            
            if not already_dug:
                self.is_digging = True
                self.dig_timer = self.dig_duration
    
    def activate_gimmick(self, gimmick):
        """기믹 활성화 - 최신 효과로 대체"""
        gimmick.is_active = False
        
        if gimmick.type == 'teleport':
            # 순간이동: 4층 아래로
            self.current_floor = min(self.current_floor + 4, TOTAL_FLOORS - 1)
            # 순간이동 후 안전을 위해 1층 동안 투명화 효과 부여
            self.is_invisible = True
            self.invisible_end_floor = self.current_floor + 1
                
        elif gimmick.type == 'invisible':
            # 투명화: 2층 동안 유지 (기존 효과 대체)
            self.is_invisible = True
            self.invisible_end_floor = self.current_floor + 2
            
        elif gimmick.type == 'slow':
            # 감속: 3초 동안 50% 감소 (기존 속도 효과 대체)
            self.speed_multiplier = 0.5
            self.speed_effect_timer = 180  # 3초 (완전히 리셋)
            
        elif gimmick.type == 'speed':
            # 가속: 3초 동안 50% 증가 (기존 속도 효과 대체)
            self.speed_multiplier = 1.5
            self.speed_effect_timer = 180  # 3초 (완전히 리셋)
            
        elif gimmick.type == 'stun':
            # 마비: 2초 정지 (기존 마비 효과 대체)
            self.is_stunned = True
            self.stun_timer = 120  # 2초 (완전히 리셋)
    
    def update(self, floors):
        """플레이어 업데이트"""
        if self.is_digging:
            self.dig_timer -= 1
            if self.dig_timer <= 0:
                self.is_digging = False
                hole_margin = 10
                hole_start = self.x - hole_margin
                hole_end = self.x + self.width + hole_margin
                floors[self.current_floor]['holes'].append((hole_start, hole_end))
        
        # 마비 타이머
        if self.is_stunned:
            self.stun_timer -= 1
            if self.stun_timer <= 0:
                self.is_stunned = False
        
        # 속도 효과 타이머
        if self.speed_effect_timer > 0:
            self.speed_effect_timer -= 1
            if self.speed_effect_timer <= 0:
                self.speed_multiplier = 1.0
    
    def draw(self, screen, camera_y):
        """플레이어 그리기"""
        y_pos = GAME_FIELD_Y + self.current_floor * FLOOR_HEIGHT + 10 - camera_y
        
        # 그림자
        shadow_surf = pygame.Surface((self.width + 10, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, self.width + 10, 8))
        screen.blit(shadow_surf, (self.x - 5, y_pos + self.height))
        
        # 투명화 상태
        if self.is_invisible:
            alpha = 100
            glow_color = GIMMICK_INVISIBLE + (80,)
            glow_surf = pygame.Surface((self.width + 30, self.height + 30), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, glow_color, (self.width // 2 + 15, self.height // 2 + 15), self.width // 2 + 15)
            screen.blit(glow_surf, (self.x - 15, y_pos - 15))
        else:
            alpha = 255
        
        # 마비 상태 표시
        if self.is_stunned:
            stun_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.circle(stun_surf, (100, 100, 255, 100), (self.width // 2 + 10, self.height // 2 + 10), self.width // 2 + 10)
            screen.blit(stun_surf, (self.x - 10, y_pos - 10))
        
        # 속도 효과 표시
        if self.speed_multiplier != 1.0:
            effect_color = GIMMICK_SPEED if self.speed_multiplier > 1.0 else GIMMICK_SLOW
            effect_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.circle(effect_surf, effect_color + (50,), (self.width // 2 + 10, self.height // 2 + 10), self.width // 2 + 10)
            screen.blit(effect_surf, (self.x - 10, y_pos - 10))
        
        if self.is_digging:
            shovel_angle = (self.dig_timer % 20) - 10
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, WARNING + (50,), (self.width//2 + 10, self.height//2 + 10), self.width//2 + 10)
            screen.blit(glow_surf, (self.x - 10, y_pos - 10))
            
            body_rect = pygame.Rect(self.x + 5, y_pos + 20, self.width - 10, self.height - 25)
            draw_rounded_rect(screen, PLAYER_COLOR, body_rect, 8)
            pygame.draw.circle(screen, (255, 220, 177), (int(self.x + self.width//2), int(y_pos + 15)), 15)
            pygame.draw.circle(screen, (245, 210, 167), (int(self.x + self.width//2), int(y_pos + 15)), 15, 2)
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + self.width//2 - 5), int(y_pos + 13)), 2)
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + self.width//2 + 5), int(y_pos + 13)), 2)
            
            shovel_x = self.x + self.width
            shovel_y = y_pos + 20 + shovel_angle
            pygame.draw.line(screen, (101, 67, 33), (shovel_x, shovel_y), (shovel_x + 30, shovel_y + 30), 5)
            pygame.draw.polygon(screen, (156, 163, 175), [(shovel_x + 30, shovel_y + 30), (shovel_x + 45, shovel_y + 35), (shovel_x + 35, shovel_y + 45)])
        else:
            body_rect = pygame.Rect(self.x + 5, y_pos + 20, self.width - 10, self.height - 25)
            draw_rounded_rect(screen, PLAYER_COLOR, body_rect, 8)
            pygame.draw.circle(screen, (255, 220, 177), (int(self.x + self.width//2), int(y_pos + 15)), 15)
            pygame.draw.circle(screen, (245, 210, 167), (int(self.x + self.width//2), int(y_pos + 15)), 15, 2)
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + self.width//2 - 5), int(y_pos + 13)), 2)
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + self.width//2 + 5), int(y_pos + 13)), 2)
            pygame.draw.line(screen, (101, 67, 33), (self.x + self.width + 5, y_pos + 30), (self.x + self.width + 5, y_pos + 55), 5)
            pygame.draw.polygon(screen, (156, 163, 175), [(self.x + self.width + 5, y_pos + 55), (self.x + self.width + 15, y_pos + 60), (self.x + self.width + 5, y_pos + 65)])
    
    def get_rect(self):
        """충돌 감지용"""
        return pygame.Rect(self.x, GAME_FIELD_Y + self.current_floor * FLOOR_HEIGHT + 10, self.width, self.height)

class Monster:
    """몬스터 클래스"""
    def __init__(self, floor_num, monster_type):
        self.floor = floor_num
        self.type = monster_type
        self.x = random.randint(100, SCREEN_WIDTH - 100)
        self.y = GAME_FIELD_Y + floor_num * FLOOR_HEIGHT + 15
        self.width = MONSTER_SIZE
        self.height = MONSTER_SIZE
        
        underground_level = max(0, floor_num - 1)
        base_speed = 1 + (underground_level // 3) * 0.5
        
        # 난이도 조정: 1~9층 14.5% 감소, 10~40층 18.8% 감소, 41~50층 27.8% 감소
        if floor_num >= 41:
            base_speed *= 0.722  # 24% + 5% 추가 감소
        elif floor_num >= 10:
            base_speed *= 0.8123  # 14.5% + 5% 추가 감소
        elif floor_num >= 1:
            base_speed *= 0.855  # 14.5% 감소
        
        self.speed = base_speed
        self.direction = random.choice([-1, 1])
        
        # 41층 이상 랜덤 방향 전환
        self.can_random_turn = floor_num >= 41
        self.turn_cooldown = 0
        
    def update(self):
        """몬스터 이동"""
        self.x += self.speed * self.direction
        
        # 벽에 닿으면 방향 전환 및 위치 조정
        if self.x <= 50:
            self.x = 50
            self.direction = 1
        elif self.x >= SCREEN_WIDTH - self.width - 50:
            self.x = SCREEN_WIDTH - self.width - 50
            self.direction = -1
        
        # 랜덤 방향 전환 (41층 이상)
        if self.can_random_turn and self.turn_cooldown <= 0:
            if random.random() < 0.01:  # 1% 확률
                self.direction *= -1
                self.turn_cooldown = 60  # 쿨다운
        
        if self.turn_cooldown > 0:
            self.turn_cooldown -= 1
    
    def draw(self, screen, camera_y):
        """몬스터 그리기"""
        y_pos = self.y - camera_y
        
        shadow_surf = pygame.Surface((self.width + 10, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, self.width + 10, 8))
        screen.blit(shadow_surf, (self.x - 5, y_pos + self.height))
        
        if self.type == 'skeleton':
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, SKELETON_COLOR + (30,), (self.width//2 + 10, self.height//2 + 10), self.width//2 + 10)
            screen.blit(glow_surf, (self.x - 10, y_pos - 10))
            
            pygame.draw.circle(screen, SKELETON_COLOR, (int(self.x + self.width//2), int(y_pos + 15)), 15)
            pygame.draw.circle(screen, (203, 213, 225), (int(self.x + self.width//2), int(y_pos + 15)), 15, 2)
            body_rect = pygame.Rect(self.x + 10, y_pos + 25, self.width - 20, self.height - 30)
            draw_rounded_rect(screen, SKELETON_COLOR, body_rect, 5)
            pygame.draw.circle(screen, DANGER, (int(self.x + 15), int(y_pos + 12)), 4)
            pygame.draw.circle(screen, DANGER, (int(self.x + 35), int(y_pos + 12)), 4)
            
        elif self.type == 'bat':
            wing_offset = abs((pygame.time.get_ticks() // 100) % 20 - 10)
            glow_surf = pygame.Surface((self.width + 40, self.height + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, BAT_COLOR + (40,), (0, 0, self.width + 40, self.height + 20))
            screen.blit(glow_surf, (self.x - 20, y_pos + 10))
            
            pygame.draw.ellipse(screen, BAT_COLOR, (self.x + 5, y_pos + 15, self.width - 10, 25))
            left_wing = [(self.x + 5, y_pos + 25), (self.x - 15, y_pos + 20 + wing_offset), (self.x + 5, y_pos + 35)]
            pygame.draw.polygon(screen, BAT_COLOR, left_wing)
            pygame.draw.polygon(screen, INFO, left_wing, 2)
            right_wing = [(self.x + self.width - 5, y_pos + 25), (self.x + self.width + 15, y_pos + 20 + wing_offset), (self.x + self.width - 5, y_pos + 35)]
            pygame.draw.polygon(screen, BAT_COLOR, right_wing)
            pygame.draw.polygon(screen, INFO, right_wing, 2)
            
        elif self.type == 'zombie':
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, ZOMBIE_COLOR + (40,), (self.width//2 + 10, self.height//2 + 10), self.width//2 + 10)
            screen.blit(glow_surf, (self.x - 10, y_pos - 10))
            
            body_rect = pygame.Rect(self.x + 5, y_pos + 20, self.width - 10, self.height - 25)
            draw_rounded_rect(screen, ZOMBIE_COLOR, body_rect, 5)
            pygame.draw.circle(screen, (52, 211, 153), (int(self.x + self.width//2), int(y_pos + 15)), 15)
            pygame.draw.circle(screen, ZOMBIE_COLOR, (int(self.x + self.width//2), int(y_pos + 15)), 15, 2)
            pygame.draw.circle(screen, DANGER, (int(self.x + 15), int(y_pos + 12)), 5)
            pygame.draw.circle(screen, DANGER, (int(self.x + 35), int(y_pos + 12)), 5)
            
        elif self.type == 'dracula':
            glow_surf = pygame.Surface((self.width + 25, self.height + 25), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, DRACULA_COLOR + (50,), (self.width//2 + 12, self.height//2 + 12), self.width//2 + 12)
            screen.blit(glow_surf, (self.x - 12, y_pos - 12))
            
            # 망토
            pygame.draw.polygon(screen, (50, 10, 10), [(self.x, y_pos + 20), (self.x + self.width, y_pos + 20), (self.x + self.width + 10, y_pos + 50), (self.x - 10, y_pos + 50)])
            
            body_rect = pygame.Rect(self.x + 8, y_pos + 22, self.width - 16, self.height - 27)
            draw_rounded_rect(screen, DRACULA_COLOR, body_rect, 5)
            pygame.draw.circle(screen, (245, 220, 177), (int(self.x + self.width//2), int(y_pos + 15)), 15)
            pygame.draw.circle(screen, DRACULA_COLOR, (int(self.x + self.width//2), int(y_pos + 15)), 15, 2)
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x + 15), int(y_pos + 12)), 4)
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x + 35), int(y_pos + 12)), 4)
            
        elif self.type == 'orc':
            glow_surf = pygame.Surface((self.width + 22, self.height + 22), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, ORC_COLOR + (45,), (self.width//2 + 11, self.height//2 + 11), self.width//2 + 11)
            screen.blit(glow_surf, (self.x - 11, y_pos - 11))
            
            body_rect = pygame.Rect(self.x + 3, y_pos + 18, self.width - 6, self.height - 23)
            draw_rounded_rect(screen, ORC_COLOR, body_rect, 6)
            pygame.draw.circle(screen, (34, 139, 34), (int(self.x + self.width//2), int(y_pos + 15)), 17)
            pygame.draw.circle(screen, ORC_COLOR, (int(self.x + self.width//2), int(y_pos + 15)), 17, 2)
            # 송곳니
            pygame.draw.polygon(screen, (255, 255, 255), [(self.x + 18, y_pos + 20), (self.x + 20, y_pos + 25), (self.x + 22, y_pos + 20)])
            pygame.draw.polygon(screen, (255, 255, 255), [(self.x + 28, y_pos + 20), (self.x + 30, y_pos + 25), (self.x + 32, y_pos + 20)])
            pygame.draw.circle(screen, (255, 50, 50), (int(self.x + 15), int(y_pos + 12)), 5)
            pygame.draw.circle(screen, (255, 50, 50), (int(self.x + 35), int(y_pos + 12)), 5)
    
    def get_rect(self):
        """충돌 감지용"""
        return pygame.Rect(self.x, self.y + 10, self.width, self.height - 10)

class Game:
    """게임 메인 클래스"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🎮 땅굴파기 게임 - 공주 구출 대작전")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "playing"
        
        self.start_time = pygame.time.get_ticks()
        self.elapsed_time = 0
        self.final_time = 0
        
        self.ranking_file = "ranking.json"
        self.player_name = ""
        self.is_new_record = False
        self.rankings = self.load_rankings()
        
        # 폰트: 웹/배포에서도 한글이 깨지지 않도록 프로젝트 포함 폰트를 우선 사용
        self.font_large = get_game_font(60)
        self.font_medium = get_game_font(32)
        self.font_small = get_game_font(24)
        self.font_tiny = get_game_font(20)
        self.font_micro = get_game_font(16)
        
        self.player = Player(SCREEN_WIDTH // 2 - PLAYER_SIZE // 2, 10)
        self.floors = self.init_floors()
        self.monsters = self.init_monsters()
        self.gimmicks = self.init_gimmicks()
        self.camera_y = 0
        
        # View 모드
        self.view_mode = False
        self.manual_camera_y = 0
        self.camera_scroll_speed = 20
    
    def init_floors(self):
        """층 초기화"""
        floors = []
        for i in range(TOTAL_FLOORS):
            floors.append({'floor_num': i, 'holes': []})
        return floors
    
    def init_gimmicks(self):
        """기믹 초기화"""
        gimmicks = []
        gimmick_positions = {
            'teleport': [6, 20, 28, 42],
            'invisible': [5, 13, 34, 45],
            'slow': [5, 14, 31, 46],
            'speed': [8, 24, 37],
            'stun': [3, 11, 22, 31, 45]
        }
        
        for gimmick_type, floors in gimmick_positions.items():
            for floor in floors:
                # 랜덤 x 위치 (몬스터와 겹치지 않도록)
                x_pos = random.randint(100, SCREEN_WIDTH - 180)
                gimmicks.append(Gimmick(floor, gimmick_type, x_pos))
        
        return gimmicks
    
    def init_monsters(self):
        """몬스터 초기화"""
        monsters = []
        for i in range(TOTAL_FLOORS):
            if i == 0 or i == TOTAL_FLOORS - 1:  # 지상(0층)과 최종층(50층)은 몬스터 없음
                continue
            
            floor_level = i - 1
            if floor_level < 10:
                monster_type = 'skeleton'
            elif floor_level < 20:
                monster_type = 'bat'
            elif floor_level < 30:
                monster_type = 'zombie'
            elif floor_level < 40:
                monster_type = 'dracula'
            else:
                monster_type = 'orc'
            
            num_monsters = random.randint(1, 2)
            for _ in range(num_monsters):
                monsters.append(Monster(i, monster_type))
        
        return monsters
    
    def load_rankings(self):
        """랭킹 로드"""
        if os.path.exists(self.ranking_file):
            try:
                with open(self.ranking_file, 'r', encoding='utf-8') as f:
                    rankings = json.load(f)
                    # 기존 랭킹에 floor 정보가 없으면 추가 (하위 호환성)
                    for rank in rankings:
                        if 'floor' not in rank:
                            rank['floor'] = 50  # 기존 데이터는 클리어 기록으로 간주
                    return rankings
            except:
                return []
        return []
    
    def save_rankings(self):
        """랭킹 저장"""
        try:
            with open(self.ranking_file, 'w', encoding='utf-8') as f:
                json.dump(self.rankings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"랭킹 저장 실패: {e}")
    
    def check_ranking(self, floor, time_seconds):
        """랭킹 진입 체크 (층수 우선, 같으면 시간)"""
        if len(self.rankings) < 3:
            return True
        # 3위 기록과 비교
        third_place = self.rankings[2]
        if floor > third_place['floor']:
            return True
        elif floor == third_place['floor'] and time_seconds < third_place['time']:
            return True
        return False
    
    def add_ranking(self, name, floor, time_seconds):
        """랭킹 추가"""
        self.rankings.append({'name': name, 'floor': floor, 'time': time_seconds})
        # 정렬: 1순위 층수(내림차순), 2순위 시간(오름차순)
        self.rankings.sort(key=lambda x: (-x['floor'], x['time']))
        self.rankings = self.rankings[:3]
        self.save_rankings()
    
    def format_time(self, milliseconds):
        """시간 포맷팅"""
        total_seconds = milliseconds / 1000
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        ms = int((milliseconds % 1000) / 10)
        return f"{minutes:02d}:{seconds:02d}.{ms:02d}"
    
    def toggle_view_mode(self):
        """View 모드 ON/OFF"""
        self.view_mode = not self.view_mode
        if not self.view_mode:
            # View 모드 OFF: 플레이어 위치로 카메라 복귀
            available_height = SCREEN_HEIGHT - GAME_FIELD_Y
            target_camera_y = self.player.current_floor * FLOOR_HEIGHT - available_height // 3
            max_camera_y = TOTAL_FLOORS * FLOOR_HEIGHT - available_height + GAME_FIELD_Y
            self.camera_y = max(0, min(target_camera_y, max_camera_y))
        else:
            # View 모드 ON: 현재 카메라 위치를 수동 카메라에 복사
            self.manual_camera_y = self.camera_y
    
    def handle_input(self):
        """입력 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # 마우스 클릭으로 View 버튼
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_state == "playing":
                    mouse_pos = pygame.mouse.get_pos()
                    view_button_rect = pygame.Rect(170, 10, 100, 70)
                    if view_button_rect.collidepoint(mouse_pos):
                        self.toggle_view_mode()
            
            # 마우스 휠로 카메라 스크롤 (View 모드)
            if event.type == pygame.MOUSEWHEEL and self.view_mode and self.game_state == "playing":
                self.manual_camera_y -= event.y * 50
                max_camera_y = TOTAL_FLOORS * FLOOR_HEIGHT - (SCREEN_HEIGHT - GAME_FIELD_Y) + GAME_FIELD_Y
                self.manual_camera_y = max(0, min(self.manual_camera_y, max_camera_y))
            
            if event.type == pygame.KEYDOWN:
                if self.game_state == "playing":
                    if event.key == pygame.K_l:
                        self.player.start_digging(self.floors, self.gimmicks)
                    elif event.key == pygame.K_s:
                        self.player.move_down(self.floors)
                    elif event.key == pygame.K_SPACE:
                        self.player.jump()
                    elif event.key == pygame.K_v:  # V 키로도 토글 가능
                        self.toggle_view_mode()
                    elif event.key == pygame.K_t and DEV_TOOLS_ENABLED:  # T 키: 테스트 모드 (개발 기능)
                        print("🧪 테스트 모드: 48층으로 이동 + 투명화 활성화")
                        self.player.current_floor = 48
                        # 테스트 모드: 투명화 상태 유지 (몬스터와 충돌 안 함)
                        self.player.is_invisible = True
                        self.player.invisible_end_floor = 999  # 매우 큰 값으로 설정하여 계속 유지
                        # 48층, 49층에 구멍 생성 (클리어 진행 가능하도록)
                        for test_floor in [48, 49]:
                            if not self.floors[test_floor]['holes']:
                                self.floors[test_floor]['holes'].append((self.player.x - 10, self.player.x + self.player.width + 10))
                
                elif self.game_state == "name_input":
                    if event.key == pygame.K_RETURN and len(self.player_name) > 0:
                        self.add_ranking(self.player_name, self.player.current_floor, self.final_time / 1000)
                        # 클리어 성공 여부 체크 (50층 도달)
                        if self.player.current_floor >= TOTAL_FLOORS - 1:
                            self.game_state = "clear"
                        else:
                            self.game_state = "gameover"
                    elif event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif event.unicode and len(self.player_name) < 10:
                        if event.unicode.isprintable():
                            self.player_name += event.unicode
                
                if event.key == pygame.K_r and self.game_state in ["gameover", "clear"]:
                    self.__init__()
                    
                if event.key == pygame.K_ESCAPE:
                    self.running = False
        
        if self.game_state == "playing":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                self.player.move(-1, self.floors)
            if keys[pygame.K_d]:
                self.player.move(1, self.floors)
            
            # View 모드에서 키보드로 카메라 이동
            if self.view_mode:
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    self.manual_camera_y -= self.camera_scroll_speed
                    self.manual_camera_y = max(0, self.manual_camera_y)
                if keys[pygame.K_DOWN]:
                    max_camera_y = TOTAL_FLOORS * FLOOR_HEIGHT - (SCREEN_HEIGHT - GAME_FIELD_Y) + GAME_FIELD_Y
                    self.manual_camera_y += self.camera_scroll_speed
                    self.manual_camera_y = min(self.manual_camera_y, max_camera_y)
    
    def update(self):
        """게임 업데이트"""
        if self.game_state == "playing":
            self.elapsed_time = pygame.time.get_ticks() - self.start_time
            
            self.player.update(self.floors)
            
            for monster in self.monsters:
                monster.update()
            
            self.check_collisions()
            
            # 카메라 업데이트 (View 모드에 따라)
            if self.view_mode:
                # View 모드: 수동 카메라 사용
                self.camera_y = self.manual_camera_y
            else:
                # 일반 모드: 플레이어 추적
                available_height = SCREEN_HEIGHT - GAME_FIELD_Y
                target_camera_y = self.player.current_floor * FLOOR_HEIGHT - available_height // 3
                max_camera_y = TOTAL_FLOORS * FLOOR_HEIGHT - available_height + GAME_FIELD_Y
                self.camera_y = max(0, min(target_camera_y, max_camera_y))
            
            # 지하 50층 도달
            if self.player.current_floor >= TOTAL_FLOORS - 1:
                self.final_time = self.elapsed_time
                if self.check_ranking(self.player.current_floor, self.final_time / 1000):
                    self.is_new_record = True
                    self.game_state = "name_input"
                else:
                    self.is_new_record = False
                    self.game_state = "clear"
    
    def check_collisions(self):
        """충돌 감지"""
        if self.player.is_invisible:
            return
        
        player_rect = self.player.get_rect()
        
        for monster in self.monsters:
            if monster.floor == self.player.current_floor:
                monster_rect = monster.get_rect()
                if player_rect.colliderect(monster_rect):
                    # 게임오버 시에도 기록 저장
                    self.final_time = self.elapsed_time
                    if self.check_ranking(self.player.current_floor, self.final_time / 1000):
                        self.is_new_record = True
                        self.game_state = "name_input"
                    else:
                        self.is_new_record = False
                        self.game_state = "gameover"
                    return
    
    def draw(self):
        """화면 그리기"""
        # 그라디언트 배경
        for y in range(SCREEN_HEIGHT):
            alpha = y / SCREEN_HEIGHT
            r = int(BG_DARKER[0] + (BG_DARK[0] - BG_DARKER[0]) * alpha)
            g = int(BG_DARKER[1] + (BG_DARK[1] - BG_DARKER[1]) * alpha)
            b = int(BG_DARKER[2] + (BG_DARK[2] - BG_DARKER[2]) * alpha)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        # 층 그리기
        for floor in self.floors:
            floor_num = floor['floor_num']
            y_pos = GAME_FIELD_Y + floor_num * FLOOR_HEIGHT - self.camera_y
            
            if GAME_FIELD_Y - FLOOR_HEIGHT <= y_pos <= SCREEN_HEIGHT:
                if floor_num == 0:
                    base_color = GROUND_SURFACE
                    dark_color = GROUND_SURFACE_DARK
                else:
                    base_color = GROUND_UNDERGROUND
                    dark_color = GROUND_UNDERGROUND_DARK
                
                floor_rect = pygame.Rect(55, y_pos + 5, SCREEN_WIDTH - 110, FLOOR_HEIGHT - 10)
                
                for i in range(FLOOR_HEIGHT - 10):
                    alpha = i / (FLOOR_HEIGHT - 10)
                    r = int(base_color[0] + (dark_color[0] - base_color[0]) * alpha)
                    g = int(base_color[1] + (dark_color[1] - base_color[1]) * alpha)
                    b = int(base_color[2] + (dark_color[2] - base_color[2]) * alpha)
                    pygame.draw.line(self.screen, (r, g, b), (55, y_pos + 5 + i), (SCREEN_WIDTH - 55, y_pos + 5 + i))
                
                for hole_start, hole_end in floor['holes']:
                    hole_width = hole_end - hole_start
                    hole_rect = pygame.Rect(hole_start, y_pos, hole_width, FLOOR_HEIGHT)
                    if hole_rect.right > 55 and hole_rect.left < SCREEN_WIDTH - 55:
                        draw_rounded_rect(self.screen, HOLE_COLOR, hole_rect, 10, 3, CARD_BORDER)
                        for i in range(FLOOR_HEIGHT - 6):
                            alpha = i / FLOOR_HEIGHT
                            shade = int(23 + 20 * alpha)
                            pygame.draw.line(self.screen, (shade, shade, shade), (hole_start + 10, y_pos + 3 + i), (hole_start + hole_width - 10, y_pos + 3 + i))
                
                pygame.draw.rect(self.screen, CARD_BORDER, floor_rect, 2, border_radius=8)
                
                if floor_num == 0:
                    floor_label = "지상"
                    label_color = SUCCESS
                    label_width = 38
                elif floor_num == TOTAL_FLOORS - 1:
                    floor_label = "B50"
                    label_color = (255, 192, 203)  # 공주가 있는 층이므로 분홍색 유지
                    label_width = 42
                else:
                    floor_label = f"B{floor_num}"
                    label_color = TEXT_SECONDARY
                    label_width = 38 if floor_num < 10 else 42
                
                label_bg = pygame.Rect(10, y_pos + FLOOR_HEIGHT // 2 - 12, label_width, 24)
                draw_rounded_rect(self.screen, CARD_BG, label_bg, 5)
                pygame.draw.rect(self.screen, CARD_BORDER, label_bg, 1, border_radius=5)
                
                floor_text = self.font_micro.render(floor_label, True, label_color)
                text_rect = floor_text.get_rect(center=(label_bg.centerx, label_bg.centery))
                self.screen.blit(floor_text, text_rect)
        
        # 기믹 그리기
        for gimmick in self.gimmicks:
            gimmick.draw(self.screen, self.camera_y)
        
        # 몬스터 그리기
        for monster in self.monsters:
            monster_y = monster.y - self.camera_y
            if GAME_FIELD_Y - FLOOR_HEIGHT <= monster_y <= SCREEN_HEIGHT:
                monster.draw(self.screen, self.camera_y)
        
        # 플레이어 그리기
        self.player.draw(self.screen, self.camera_y)
        
        # 공주 그리기 (50층)
        if self.player.current_floor >= TOTAL_FLOORS - 1:
            self.draw_princess()
        
        self.draw_ui()
        
        if self.game_state == "gameover":
            self.draw_gameover()
        elif self.game_state == "name_input":
            self.draw_name_input()
        elif self.game_state == "clear":
            self.draw_clear()
        
        pygame.display.flip()
    
    def draw_princess(self):
        """공주 그리기"""
        y_pos = GAME_FIELD_Y + (TOTAL_FLOORS - 1) * FLOOR_HEIGHT + 20 - self.camera_y
        princess_x = SCREEN_WIDTH // 2 + 100
        
        # 공주 (분홍색 드레스)
        pygame.draw.circle(self.screen, (255, 220, 177), (princess_x, int(y_pos + 15)), 15)
        pygame.draw.polygon(self.screen, (255, 192, 203), [(princess_x - 20, y_pos + 30), (princess_x + 20, y_pos + 30), (princess_x + 25, y_pos + 55), (princess_x - 25, y_pos + 55)])
        
        # 하트
        heart_x = (self.player.x + princess_x) // 2
        heart_y = y_pos + 20
        pygame.draw.circle(self.screen, (255, 0, 127), (heart_x - 8, heart_y), 10)
        pygame.draw.circle(self.screen, (255, 0, 127), (heart_x + 8, heart_y), 10)
        pygame.draw.polygon(self.screen, (255, 0, 127), [(heart_x - 18, heart_y), (heart_x, heart_y + 20), (heart_x + 18, heart_y)])
    
    def draw_ui(self):
        """UI 그리기"""
        pygame.draw.rect(self.screen, BG_DARK, (0, 0, SCREEN_WIDTH, UI_HEIGHT))
        
        gradient_surf = pygame.Surface((SCREEN_WIDTH, 5), pygame.SRCALPHA)
        for i in range(5):
            alpha = int(100 - (i * 20))
            color = CARD_BORDER + (alpha,)
            pygame.draw.line(gradient_surf, color, (0, i), (SCREEN_WIDTH, i))
        self.screen.blit(gradient_surf, (0, UI_HEIGHT - 5))
        
        # 왼쪽 카드: 현재 층 정보 (크기 축소)
        left_card = pygame.Rect(10, 10, 150, 70)
        draw_rounded_rect(self.screen, CARD_BG, left_card, 10, 2, CARD_BORDER)
        
        if self.player.current_floor == 0:
            floor_display = "지상"
            floor_color = SUCCESS
        else:
            floor_display = f"B{self.player.current_floor}"
            floor_color = PRIMARY
        
        floor_label = self.font_micro.render("위치", True, TEXT_MUTED)
        floor_text = self.font_micro.render(floor_display, True, floor_color)
        goal_text = self.font_micro.render("→ B50", True, TEXT_SECONDARY)
        
        self.screen.blit(floor_label, (20, 16))
        self.screen.blit(floor_text, (20, 35))
        self.screen.blit(goal_text, (20, 63))
        
        # View 버튼 카드 (현재 위치 옆)
        view_button_rect = pygame.Rect(170, 10, 100, 70)
        
        # View 모드에 따라 버튼 색상 변경
        if self.view_mode:
            button_color = PRIMARY
            border_color = PRIMARY_HOVER
            text_color = TEXT_PRIMARY
            status_text = "ON"
        else:
            button_color = CARD_BG
            border_color = CARD_BORDER
            text_color = TEXT_SECONDARY
            status_text = "OFF"
        
        # 마우스 호버 효과
        mouse_pos = pygame.mouse.get_pos()
        is_hovering = view_button_rect.collidepoint(mouse_pos)
        if is_hovering:
            button_color = tuple(min(c + 20, 255) for c in button_color[:3])
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
        draw_rounded_rect(self.screen, button_color, view_button_rect, 10, 2, border_color)
        
        # 버튼 내용 (이모지 대신 텍스트 사용)
        view_label = self.font_micro.render("VIEW", True, TEXT_MUTED)
        mode_label = self.font_micro.render("전체맵", True, text_color)
        status_label = self.font_micro.render(status_text, True, text_color)
        
        self.screen.blit(view_label, (178, 14))
        self.screen.blit(mode_label, (178, 33))
        self.screen.blit(status_label, (178, 54))
        
        # 중앙 카드: 타이머
        center_card = pygame.Rect(280, 10, 200, 70)
        draw_rounded_rect(self.screen, CARD_BG, center_card, 10, 2, WARNING)
        
        time_display = self.format_time(self.elapsed_time)
        timer_label = self.font_micro.render("⏱ TIMER", True, TEXT_MUTED)
        time_text = self.font_medium.render(time_display, True, WARNING)
        
        timer_rect = timer_label.get_rect(center=(380, 22))
        time_rect = time_text.get_rect(center=(380, 52))
        
        glow_surf = pygame.Surface((time_text.get_width() + 40, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, WARNING + (30,), (0, 0, time_text.get_width() + 40, 40))
        self.screen.blit(glow_surf, (time_rect.x - 20, time_rect.y - 5))
        
        self.screen.blit(timer_label, timer_rect)
        self.screen.blit(time_text, time_rect)
        
        # 우측 카드: 조작법
        right_card = pygame.Rect(490, 10, 300, 70)
        draw_rounded_rect(self.screen, CARD_BG, right_card, 10, 2, CARD_BORDER)
        
        controls_label = self.font_micro.render("조작법", True, TEXT_MUTED)
        control_line1 = self.font_micro.render("이동: A , D  내려가기: S  파기: L", True, TEXT_SECONDARY)
        control_line2 = self.font_micro.render("점프: Space  View 모드: V key", True, TEXT_SECONDARY)
        
        self.screen.blit(controls_label, (500, 14))
        self.screen.blit(control_line1, (500, 36))
        self.screen.blit(control_line2, (500, 58))
    
    def draw_gameover(self):
        """게임 오버 화면"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            alpha = int(180 + (y / SCREEN_HEIGHT) * 60)
            pygame.draw.line(overlay, BG_DARKER + (alpha,), (0, y), (SCREEN_WIDTH, y))
        self.screen.blit(overlay, (0, 0))
        
        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150, 500, 300)
        shadow_surf = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        self.screen.blit(shadow_surf, (card_rect.x + 8, card_rect.y + 8))
        draw_rounded_rect(self.screen, CARD_BG, card_rect, 20, 3, DANGER)
        
        pulse = abs(((pygame.time.get_ticks() // 10) % 100) - 50) / 50
        glow_size = int(100 + pulse * 50)
        glow_surf = pygame.Surface((glow_size * 3, glow_size), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, DANGER + (50,), (0, 0, glow_size * 3, glow_size))
        self.screen.blit(glow_surf, (SCREEN_WIDTH // 2 - glow_size * 1.5, SCREEN_HEIGHT // 2 - 100 - glow_size // 2))
        
        gameover_text = self.font_large.render("💀 GAME OVER", True, DANGER)
        text_rect = gameover_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70))
        self.screen.blit(gameover_text, text_rect)
        
        pygame.draw.line(self.screen, CARD_BORDER, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 10), (SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 - 10), 2)
        
        # 도달한 층과 플레이 타임 표시
        floor_num = self.player.current_floor
        if floor_num == 0:
            floor_str = "지상"
        else:
            floor_str = f"B{floor_num}"
        
        floor_label = self.font_small.render("도달한 층", True, TEXT_MUTED)
        floor_text = self.font_medium.render(floor_str, True, INFO)
        
        floor_label_rect = floor_label.get_rect(center=(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20))
        floor_rect = floor_text.get_rect(center=(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50))
        
        self.screen.blit(floor_label, floor_label_rect)
        self.screen.blit(floor_text, floor_rect)
        
        time_display = self.format_time(self.final_time)
        time_label = self.font_small.render("플레이 타임", True, TEXT_MUTED)
        time_text = self.font_medium.render(time_display, True, PRIMARY)
        
        time_label_rect = time_label.get_rect(center=(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 20))
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 + 50))
        
        self.screen.blit(time_label, time_label_rect)
        self.screen.blit(time_text, time_rect)
        
        restart_label = self.font_small.render("다시 도전하기", True, TEXT_MUTED)
        restart_text = self.font_medium.render("R 키", True, PRIMARY)
        
        restart_label_rect = restart_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 140))
        
        self.screen.blit(restart_label, restart_label_rect)
        self.screen.blit(restart_text, restart_rect)
    
    def draw_name_input(self):
        """이름 입력 화면"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            alpha = int(200 + (y / SCREEN_HEIGHT) * 40)
            pygame.draw.line(overlay, BG_DARKER + (alpha,), (0, y), (SCREEN_WIDTH, y))
        self.screen.blit(overlay, (0, 0))
        
        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT // 2 - 180, 560, 360)
        shadow_surf = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 120))
        self.screen.blit(shadow_surf, (card_rect.x + 10, card_rect.y + 10))
        draw_rounded_rect(self.screen, CARD_BG, card_rect, 25, 3, WARNING)
        
        pulse = abs(((pygame.time.get_ticks() // 10) % 100) - 50) / 50
        glow_size = int(120 + pulse * 60)
        glow_surf = pygame.Surface((glow_size * 2, glow_size), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, WARNING + (60,), (0, 0, glow_size * 2, glow_size))
        self.screen.blit(glow_surf, (SCREEN_WIDTH // 2 - glow_size, SCREEN_HEIGHT // 2 - 140 - glow_size // 2))
        
        congrats_text = self.font_large.render("🏆 신기록! 🏆", True, WARNING)
        congrats_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
        self.screen.blit(congrats_text, congrats_rect)
        
        # 도착한 층 표시
        floor_num = self.player.current_floor
        if floor_num == 0:
            floor_str = "지상"
        else:
            floor_str = f"B{floor_num}"
        floor_label = self.font_small.render("도착한 층", True, TEXT_MUTED)
        floor_color = (255, 192, 203) if floor_num >= TOTAL_FLOORS - 1 else INFO
        floor_text = self.font_medium.render(floor_str, True, floor_color)
        
        floor_label_rect = floor_label.get_rect(center=(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 60))
        floor_rect = floor_text.get_rect(center=(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 30))
        
        self.screen.blit(floor_label, floor_label_rect)
        self.screen.blit(floor_text, floor_rect)
        
        # 시간 표시
        time_display = self.format_time(self.final_time)
        time_label = self.font_small.render("플레이 타임", True, TEXT_MUTED)
        time_text = self.font_medium.render(time_display, True, PRIMARY)
        
        time_label_rect = time_label.get_rect(center=(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 - 60))
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT // 2 - 30))
        
        self.screen.blit(time_label, time_label_rect)
        self.screen.blit(time_text, time_rect)
        
        pygame.draw.line(self.screen, CARD_BORDER, (SCREEN_WIDTH // 2 - 230, SCREEN_HEIGHT // 2 + 5), (SCREEN_WIDTH // 2 + 230, SCREEN_HEIGHT // 2 + 5), 2)
        
        prompt_text = self.font_small.render("명예의 전당에 새길 이름 (최대 10글자)", True, TEXT_SECONDARY)
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 35))
        self.screen.blit(prompt_text, prompt_rect)
        
        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 70, 360, 60)
        draw_rounded_rect(self.screen, BG_DARK, input_box, 12, 3, PRIMARY)
        
        cursor_blink = (pygame.time.get_ticks() // 500) % 2
        display_name = self.player_name + ("_" if cursor_blink else "")
        name_text = self.font_medium.render(display_name, True, TEXT_PRIMARY)
        name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(name_text, name_rect)
        
        confirm_text = self.font_small.render("Enter 키를 눌러 등록", True, SUCCESS)
        confirm_rect = confirm_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self.screen.blit(confirm_text, confirm_rect)
    
    def draw_clear(self):
        """클리어 화면"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            alpha = int(200 + (y / SCREEN_HEIGHT) * 40)
            pygame.draw.line(overlay, BG_DARKER + (alpha,), (0, y), (SCREEN_WIDTH, y))
        self.screen.blit(overlay, (0, 0))
        
        time_offset = pygame.time.get_ticks() // 100
        color_r = abs(int(127 * (1 + pygame.math.Vector2(1, 0).rotate(time_offset * 10).x)))
        color_g = abs(int(127 * (1 + pygame.math.Vector2(1, 0).rotate(time_offset * 15).y)))
        color_b = 255
        
        pulse = abs(((pygame.time.get_ticks() // 10) % 100) - 50) / 50
        glow_size = int(150 + pulse * 80)
        glow_surf = pygame.Surface((glow_size * 2, glow_size), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (color_r, color_g, color_b, 80), (0, 0, glow_size * 2, glow_size))
        self.screen.blit(glow_surf, (SCREEN_WIDTH // 2 - glow_size, 60 - glow_size // 2))
        
        clear_text = self.font_large.render("★ CLEAR ★", True, (color_r, color_g, color_b))
        text_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(clear_text, text_rect)
        
        princess_text = self.font_medium.render("💖 공주를 구출했습니다! 💖", True, (255, 192, 203))
        princess_rect = princess_text.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(princess_text, princess_rect)
        
        time_card = pygame.Rect(SCREEN_WIDTH // 2 - 150, 150, 300, 70)
        draw_rounded_rect(self.screen, CARD_BG, time_card, 15, 3, SUCCESS)
        
        time_label = self.font_small.render("클리어 타임", True, TEXT_MUTED)
        time_display = self.format_time(self.final_time)
        time_text = self.font_medium.render(time_display, True, SUCCESS)
        
        time_label_rect = time_label.get_rect(center=(SCREEN_WIDTH // 2, 165))
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, 195))
        
        self.screen.blit(time_label, time_label_rect)
        self.screen.blit(time_text, time_rect)
        
        ranking_card = pygame.Rect(SCREEN_WIDTH // 2 - 280, 250, 560, 220)
        draw_rounded_rect(self.screen, CARD_BG, ranking_card, 20, 3, WARNING)
        
        ranking_title = self.font_medium.render("🏆 명예의 전당 🏆", True, WARNING)
        ranking_title_rect = ranking_title.get_rect(center=(SCREEN_WIDTH // 2, 280))
        self.screen.blit(ranking_title, ranking_title_rect)
        
        pygame.draw.line(self.screen, CARD_BORDER, (SCREEN_WIDTH // 2 - 240, 310), (SCREEN_WIDTH // 2 + 240, 310), 2)
        
        medals = ["🥇", "🥈", "🥉"]
        medal_colors = [WARNING, (192, 192, 192), (205, 127, 50)]
        
        for i, record in enumerate(self.rankings[:3]):
            y_pos = 335 + i * 45
            rank_bg = pygame.Rect(SCREEN_WIDTH // 2 - 260, y_pos - 5, 520, 35)
            if i % 2 == 0:
                draw_rounded_rect(self.screen, BG_DARK, rank_bg, 8)
            
            medal_text = self.font_medium.render(f"{medals[i]} {i+1}위", True, medal_colors[i])
            self.screen.blit(medal_text, (SCREEN_WIDTH // 2 - 240, y_pos))
            
            name_text = self.font_small.render(record['name'], True, TEXT_PRIMARY)
            self.screen.blit(name_text, (SCREEN_WIDTH // 2 - 100, y_pos + 5))
            
            # 층수 표시 (B50 또는 지상)
            floor_num = record.get('floor', 0)
            if floor_num == 0:
                floor_str = "지상"
            else:
                floor_str = f"B{floor_num}"
            floor_color = (255, 192, 203) if floor_num >= TOTAL_FLOORS - 1 else INFO
            floor_render = self.font_small.render(floor_str, True, floor_color)
            self.screen.blit(floor_render, (SCREEN_WIDTH // 2 + 20, y_pos + 5))
            
            # 시간 표시
            time_str = self.format_time(record['time'] * 1000)
            time_render = self.font_small.render(time_str, True, PRIMARY)
            time_render_rect = time_render.get_rect(right=SCREEN_WIDTH // 2 + 240, centery=y_pos + 12)
            self.screen.blit(time_render, time_render_rect)
        
        restart_card = pygame.Rect(SCREEN_WIDTH // 2 - 100, 500, 200, 50)
        draw_rounded_rect(self.screen, CARD_BG, restart_card, 12, 3, PRIMARY)
        
        restart_text = self.font_medium.render("R 키로 재시작", True, PRIMARY)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 525))
        self.screen.blit(restart_text, restart_rect)
    
    def run(self):
        """게임 실행"""
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        # 웹 빌드 환경에서는 sys.exit()가 불필요/문제가 될 수 있어 생략
        if not IS_WEB_BUILD:
            sys.exit()

if __name__ == "__main__":
    if IS_WEB_BUILD:
        # pygbag/emscripten: 브라우저 환경에서는 asyncio 이벤트 루프 기반으로 구동
        import asyncio

        async def main():
            game = Game()
            while game.running:
                game.handle_input()
                game.update()
                game.draw()
                game.clock.tick(FPS)
                await asyncio.sleep(0)
            pygame.quit()

        asyncio.run(main())
    else:
        game = Game()
        game.run()
