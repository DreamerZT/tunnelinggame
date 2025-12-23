import pygame
import sys
import random
import json
import os
from datetime import timedelta

# Pygame 초기화
pygame.init()
pygame.mixer.init()

# 게임 설정
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
UI_HEIGHT = 95  # 상단 UI 높이
GAME_FIELD_Y = UI_HEIGHT  # 게임 필드 시작 Y 위치
FLOOR_HEIGHT = 80  # 각 층의 높이
PLAYER_SIZE = 60
MONSTER_SIZE = 50
TOTAL_FLOORS = 51  # 지상 1층 + 지하 50층
FPS = 60

# 현대적인 색상 팔레트 (Tailwind 스타일)
# 배경 & 기본
BG_DARK = (15, 23, 42)  # slate-900
BG_DARKER = (2, 6, 23)  # slate-950
CARD_BG = (30, 41, 59)  # slate-800
CARD_BORDER = (51, 65, 85)  # slate-700

# 텍스트
TEXT_PRIMARY = (248, 250, 252)  # slate-50
TEXT_SECONDARY = (203, 213, 225)  # slate-300
TEXT_MUTED = (148, 163, 184)  # slate-400

# 색상
PRIMARY = (59, 130, 246)  # blue-500
PRIMARY_HOVER = (37, 99, 235)  # blue-600
SUCCESS = (34, 197, 94)  # green-500
WARNING = (234, 179, 8)  # yellow-500
DANGER = (239, 68, 68)  # red-500
INFO = (168, 85, 247)  # purple-500

# 게임 요소
PLAYER_COLOR = (96, 165, 250)  # blue-400
GROUND_SURFACE = (22, 163, 74)  # green-600
GROUND_SURFACE_DARK = (21, 128, 61)  # green-700
GROUND_UNDERGROUND = (120, 53, 15)  # brown-800
GROUND_UNDERGROUND_DARK = (87, 38, 10)  # brown-900
HOLE_COLOR = (23, 23, 23)  # neutral-900

# 몬스터
SKELETON_COLOR = (226, 232, 240)  # slate-200
BAT_COLOR = (192, 132, 252)  # purple-400
ZOMBIE_COLOR = (74, 222, 128)  # green-400
DRACULA_COLOR = (220, 38, 38)  # red-600
ORC_COLOR = (22, 101, 52)  # green-800

# 기믹 색상
GIMMICK_TELEPORT = (250, 204, 21)  # yellow-400
GIMMICK_INVISIBLE = (251, 146, 60)  # orange-400
GIMMICK_SLOW = (168, 85, 247)  # purple-500
GIMMICK_SPEED = (236, 72, 153)  # pink-500
GIMMICK_STUN = (23, 23, 23)  # neutral-900

# 이펙트
GLOW_COLOR = (96, 165, 250, 100)  # blue-400 with alpha
SHADOW_COLOR = (0, 0, 0, 80)

class Player:
    """용사 캐릭터 클래스"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_SIZE
        self.height = PLAYER_SIZE
        self.base_speed = 5
        self.speed = 5
        self.current_floor = 0  # 0층부터 시작 (지상)
        self.is_digging = False
        self.dig_timer = 0
        self.dig_duration = 60  # 1초 (60 프레임)
        
        # 상태 효과
        self.is_invisible = False  # 투명화 상태
        self.invisible_end_floor = 0  # 투명화 종료 층
        self.is_stunned = False  # 마비 상태
        self.stun_timer = 0  # 마비 시간
        self.speed_effect_timer = 0  # 속도 효과 시간
        self.speed_multiplier = 1.0  # 속도 배수
        
    def move(self, dx, floors):
        """좌우 이동"""
        # 마비 상태면 이동 불가
        if self.is_stunned:
            return
        
        # 속도 효과 적용
        actual_speed = self.base_speed * self.speed_multiplier
        new_x = self.x + dx * actual_speed
        # 화면 밖으로 나가지 않도록 제한
        if 50 <= new_x <= SCREEN_WIDTH - self.width - 50:
            self.x = new_x
    
    def move_down(self, floors):
        """아래층으로 이동 (땅굴이 파져있을 때만)"""
        if self.current_floor < TOTAL_FLOORS - 1:
            # 현재 위치에 땅굴이 파져있는지 확인
            current_holes = floors[self.current_floor]['holes']
            for hole_start, hole_end in current_holes:
                # 캐릭터가 구멍 위에 있는지 확인
                if hole_start <= self.x + self.width // 2 <= hole_end:
                    self.current_floor += 1
                    return True
        return False
    
    def jump(self):
        """위층으로 점프 (1층 위로)"""
        if self.current_floor > 0:
            self.current_floor -= 1
            return True
        return False
    
    def start_digging(self, floors):
        """땅굴 파기 시작"""
        if not self.is_digging:
            # 현재 위치에 이미 구멍이 있는지 확인
            current_holes = floors[self.current_floor]['holes']
            player_center = self.x + self.width // 2
            
            already_dug = False
            for hole_start, hole_end in current_holes:
                if hole_start <= player_center <= hole_end:
                    already_dug = True
                    break
            
            if not already_dug:
                self.is_digging = True
                self.dig_timer = self.dig_duration
            
    def update(self, floors):
        """캐릭터 상태 업데이트"""
        if self.is_digging:
            self.dig_timer -= 1
            if self.dig_timer <= 0:
                self.is_digging = False
                # 현재 위치에 구멍 추가 (캐릭터 너비만큼)
                hole_margin = 10  # 좌우 여유 공간
                hole_start = self.x - hole_margin
                hole_end = self.x + self.width + hole_margin
                floors[self.current_floor]['holes'].append((hole_start, hole_end))
    
    def draw(self, screen, camera_y):
        """캐릭터 그리기 - 현대적 디자인"""
        y_pos = GAME_FIELD_Y + self.current_floor * FLOOR_HEIGHT + 10 - camera_y
        
        # 그림자 효과
        shadow_surf = pygame.Surface((self.width + 10, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, self.width + 10, 8))
        screen.blit(shadow_surf, (self.x - 5, y_pos + self.height))
        
        # 땅굴 파는 모션
        if self.is_digging:
            shovel_angle = (self.dig_timer % 20) - 10
            
            # 글로우 효과 (파는 중)
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, WARNING + (50,), 
                             (self.width//2 + 10, self.height//2 + 10), self.width//2 + 10)
            screen.blit(glow_surf, (self.x - 10, y_pos - 10))
            
            # 캐릭터 몸체
            body_rect = pygame.Rect(self.x + 5, y_pos + 20, self.width - 10, self.height - 25)
            draw_rounded_rect(screen, PLAYER_COLOR, body_rect, 8)
            
            # 머리
            pygame.draw.circle(screen, (255, 220, 177), (int(self.x + self.width//2), int(y_pos + 15)), 15)
            pygame.draw.circle(screen, (245, 210, 167), (int(self.x + self.width//2), int(y_pos + 15)), 15, 2)
            
            # 눈
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + self.width//2 - 5), int(y_pos + 13)), 2)
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + self.width//2 + 5), int(y_pos + 13)), 2)
            
            # 삽 (움직이는 애니메이션)
            shovel_x = self.x + self.width
            shovel_y = y_pos + 20 + shovel_angle
            pygame.draw.line(screen, (101, 67, 33), (shovel_x, shovel_y), (shovel_x + 30, shovel_y + 30), 5)
            pygame.draw.polygon(screen, (156, 163, 175), [
                (shovel_x + 30, shovel_y + 30),
                (shovel_x + 45, shovel_y + 35),
                (shovel_x + 35, shovel_y + 45)
            ])
        else:
            # 일반 상태
            # 캐릭터 몸체
            body_rect = pygame.Rect(self.x + 5, y_pos + 20, self.width - 10, self.height - 25)
            draw_rounded_rect(screen, PLAYER_COLOR, body_rect, 8)
            
            # 머리
            pygame.draw.circle(screen, (255, 220, 177), (int(self.x + self.width//2), int(y_pos + 15)), 15)
            pygame.draw.circle(screen, (245, 210, 167), (int(self.x + self.width//2), int(y_pos + 15)), 15, 2)
            
            # 눈
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + self.width//2 - 5), int(y_pos + 13)), 2)
            pygame.draw.circle(screen, (50, 50, 50), (int(self.x + self.width//2 + 5), int(y_pos + 13)), 2)
            
            # 삽 (들고 있는 상태)
            pygame.draw.line(screen, (101, 67, 33), (self.x + self.width + 5, y_pos + 30), 
                           (self.x + self.width + 5, y_pos + 55), 5)
            pygame.draw.polygon(screen, (156, 163, 175), [
                (self.x + self.width + 5, y_pos + 55),
                (self.x + self.width + 15, y_pos + 60),
                (self.x + self.width + 5, y_pos + 65)
            ])
    
    def get_rect(self):
        """충돌 감지용 사각형 반환"""
        return pygame.Rect(self.x, GAME_FIELD_Y + self.current_floor * FLOOR_HEIGHT + 10, 
                          self.width, self.height)

class Monster:
    """몬스터 클래스"""
    def __init__(self, floor_num, monster_type):
        self.floor = floor_num
        self.type = monster_type  # 'skeleton', 'bat', 'zombie'
        self.x = random.randint(100, SCREEN_WIDTH - 100)
        self.y = GAME_FIELD_Y + floor_num * FLOOR_HEIGHT + 15
        self.width = MONSTER_SIZE
        self.height = MONSTER_SIZE
        
        # 층에 따라 속도 증가 (floor_num이 1부터 시작하므로 조정)
        underground_level = max(0, floor_num - 1)  # 지하 층수 (0층 제외)
        base_speed = 1 + (underground_level // 3) * 0.5
        self.speed = base_speed
        self.direction = random.choice([-1, 1])
        
    def update(self):
        """몬스터 이동 업데이트"""
        self.x += self.speed * self.direction
        
        # 화면 경계에 닿으면 방향 전환
        if self.x <= 50 or self.x >= SCREEN_WIDTH - self.width - 50:
            self.direction *= -1
    
    def draw(self, screen, camera_y):
        """몬스터 그리기 - 현대적 디자인"""
        y_pos = self.y - camera_y
        
        # 그림자 효과
        shadow_surf = pygame.Surface((self.width + 10, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, self.width + 10, 8))
        screen.blit(shadow_surf, (self.x - 5, y_pos + self.height))
        
        if self.type == 'skeleton':
            # 해골 병사 (현대적 디자인)
            # 글로우 효과
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, SKELETON_COLOR + (30,), 
                             (self.width//2 + 10, self.height//2 + 10), self.width//2 + 10)
            screen.blit(glow_surf, (self.x - 10, y_pos - 10))
            
            # 머리
            pygame.draw.circle(screen, SKELETON_COLOR, (int(self.x + self.width//2), int(y_pos + 15)), 15)
            pygame.draw.circle(screen, (203, 213, 225), (int(self.x + self.width//2), int(y_pos + 15)), 15, 2)
            
            # 몸체
            body_rect = pygame.Rect(self.x + 10, y_pos + 25, self.width - 20, self.height - 30)
            draw_rounded_rect(screen, SKELETON_COLOR, body_rect, 5)
            
            # 눈 (빛나는 효과)
            pygame.draw.circle(screen, DANGER, (int(self.x + 15), int(y_pos + 12)), 4)
            pygame.draw.circle(screen, DANGER, (int(self.x + 35), int(y_pos + 12)), 4)
            pygame.draw.circle(screen, (255, 100, 100), (int(self.x + 15), int(y_pos + 12)), 2)
            pygame.draw.circle(screen, (255, 100, 100), (int(self.x + 35), int(y_pos + 12)), 2)
            
        elif self.type == 'bat':
            # 박쥐 (현대적 디자인)
            wing_offset = abs((pygame.time.get_ticks() // 100) % 20 - 10)
            
            # 글로우 효과
            glow_surf = pygame.Surface((self.width + 40, self.height + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, BAT_COLOR + (40,), (0, 0, self.width + 40, self.height + 20))
            screen.blit(glow_surf, (self.x - 20, y_pos + 10))
            
            # 몸체
            pygame.draw.ellipse(screen, BAT_COLOR, (self.x + 5, y_pos + 15, self.width - 10, 25))
            
            # 날개 (그라디언트 효과)
            left_wing = [
                (self.x + 5, y_pos + 25),
                (self.x - 15, y_pos + 20 + wing_offset),
                (self.x + 5, y_pos + 35)
            ]
            pygame.draw.polygon(screen, BAT_COLOR, left_wing)
            pygame.draw.polygon(screen, INFO, left_wing, 2)
            
            right_wing = [
                (self.x + self.width - 5, y_pos + 25),
                (self.x + self.width + 15, y_pos + 20 + wing_offset),
                (self.x + self.width - 5, y_pos + 35)
            ]
            pygame.draw.polygon(screen, BAT_COLOR, right_wing)
            pygame.draw.polygon(screen, INFO, right_wing, 2)
            
            # 눈
            pygame.draw.circle(screen, (255, 200, 255), (int(self.x + self.width//2 - 5), int(y_pos + 23)), 3)
            pygame.draw.circle(screen, (255, 200, 255), (int(self.x + self.width//2 + 5), int(y_pos + 23)), 3)
            
        elif self.type == 'zombie':
            # 좀비 (현대적 디자인)
            # 글로우 효과
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, ZOMBIE_COLOR + (40,), 
                             (self.width//2 + 10, self.height//2 + 10), self.width//2 + 10)
            screen.blit(glow_surf, (self.x - 10, y_pos - 10))
            
            # 몸체
            body_rect = pygame.Rect(self.x + 5, y_pos + 20, self.width - 10, self.height - 25)
            draw_rounded_rect(screen, ZOMBIE_COLOR, body_rect, 5)
            
            # 머리
            pygame.draw.circle(screen, (52, 211, 153), (int(self.x + self.width//2), int(y_pos + 15)), 15)
            pygame.draw.circle(screen, ZOMBIE_COLOR, (int(self.x + self.width//2), int(y_pos + 15)), 15, 2)
            
            # 눈 (빛나는 빨간 눈)
            pygame.draw.circle(screen, DANGER, (int(self.x + 15), int(y_pos + 12)), 5)
            pygame.draw.circle(screen, DANGER, (int(self.x + 35), int(y_pos + 12)), 5)
            pygame.draw.circle(screen, (255, 150, 150), (int(self.x + 15), int(y_pos + 12)), 3)
            pygame.draw.circle(screen, (255, 150, 150), (int(self.x + 35), int(y_pos + 12)), 3)
    
    def get_rect(self):
        """충돌 감지용 사각형 반환"""
        return pygame.Rect(self.x, self.y + 10, self.width, self.height - 10)

def draw_rounded_rect(surface, color, rect, radius=10, border_width=0, border_color=None):
    """둥근 모서리 사각형 그리기"""
    x, y, w, h = rect
    
    # 메인 사각형
    pygame.draw.rect(surface, color, (x + radius, y, w - 2*radius, h))
    pygame.draw.rect(surface, color, (x, y + radius, w, h - 2*radius))
    
    # 모서리 원
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + h - radius), radius)
    pygame.draw.circle(surface, color, (x + w - radius, y + h - radius), radius)
    
    # 테두리
    if border_width > 0 and border_color:
        pygame.draw.rect(surface, border_color, (x + radius, y, w - 2*radius, border_width))
        pygame.draw.rect(surface, border_color, (x + radius, y + h - border_width, w - 2*radius, border_width))
        pygame.draw.rect(surface, border_color, (x, y + radius, border_width, h - 2*radius))
        pygame.draw.rect(surface, border_color, (x + w - border_width, y + radius, border_width, h - 2*radius))

def draw_shadow(surface, rect, offset=5, alpha=80):
    """그림자 효과 그리기"""
    shadow_surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    shadow_surf.fill((0, 0, 0, alpha))
    surface.blit(shadow_surf, (rect[0] + offset, rect[1] + offset))

class Game:
    """게임 메인 클래스"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🎮 땅굴파기 게임")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "playing"  # playing, gameover, clear, name_input
        
        # 타이머 관련
        self.start_time = pygame.time.get_ticks()
        self.elapsed_time = 0
        self.final_time = 0
        
        # 랭킹 관련
        self.ranking_file = "ranking.json"
        self.player_name = ""
        self.is_new_record = False
        self.rankings = self.load_rankings()
        
        # 폰트 설정 (한글 지원)
        try:
            # Windows 한글 폰트 사용
            self.font_large = pygame.font.SysFont('malgungothic', 60)
            self.font_medium = pygame.font.SysFont('malgungothic', 32)
            self.font_small = pygame.font.SysFont('malgungothic', 24)
            self.font_tiny = pygame.font.SysFont('malgungothic', 20)
            self.font_micro = pygame.font.SysFont('malgungothic', 16)  # 층 번호용
        except:
            # 폰트가 없을 경우 기본 폰트 사용
            self.font_large = pygame.font.Font(None, 60)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
            self.font_tiny = pygame.font.Font(None, 20)
            self.font_micro = pygame.font.Font(None, 16)
        
        # 게임 객체 초기화
        self.player = Player(SCREEN_WIDTH // 2 - PLAYER_SIZE // 2, 10)
        self.floors = self.init_floors()
        self.monsters = self.init_monsters()
        self.camera_y = 0
    
    def load_rankings(self):
        """랭킹 파일 로드"""
        if os.path.exists(self.ranking_file):
            try:
                with open(self.ranking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_rankings(self):
        """랭킹 파일 저장"""
        try:
            with open(self.ranking_file, 'w', encoding='utf-8') as f:
                json.dump(self.rankings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"랭킹 저장 실패: {e}")
    
    def check_ranking(self, time_seconds):
        """랭킹 진입 여부 확인 (1~3위)"""
        if len(self.rankings) < 3:
            return True
        return time_seconds < self.rankings[2]['time']
    
    def add_ranking(self, name, time_seconds):
        """랭킹 추가 및 정렬"""
        self.rankings.append({
            'name': name,
            'time': time_seconds
        })
        # 시간 순으로 정렬
        self.rankings.sort(key=lambda x: x['time'])
        # 상위 3개만 유지
        self.rankings = self.rankings[:3]
        self.save_rankings()
    
    def format_time(self, milliseconds):
        """시간을 포맷팅 (MM:SS.ms)"""
        total_seconds = milliseconds / 1000
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        ms = int((milliseconds % 1000) / 10)
        return f"{minutes:02d}:{seconds:02d}.{ms:02d}"
        
    def init_floors(self):
        """층 초기화"""
        floors = []
        for i in range(TOTAL_FLOORS):
            floors.append({
                'floor_num': i,
                'holes': []  # 파진 구멍들의 x 위치 리스트 [(x_start, x_end), ...]
            })
        return floors
    
    def init_monsters(self):
        """몬스터 초기화"""
        monsters = []
        for i in range(TOTAL_FLOORS):
            # 0층(지상)에는 몬스터 없음
            if i == 0:
                continue
            
            # 층별로 몬스터 타입 결정 (1층부터 시작하므로 i-1 사용)
            floor_level = i - 1  # 실제 지하 층수
            if floor_level < 10:
                monster_type = 'skeleton'
            elif floor_level < 20:
                monster_type = 'bat'
            else:
                monster_type = 'zombie'
            
            # 각 층에 몬스터 1~2마리 배치
            num_monsters = random.randint(1, 2)
            for _ in range(num_monsters):
                monsters.append(Monster(i, monster_type))
        
        return monsters
    
    def handle_input(self):
        """키보드 입력 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if self.game_state == "playing":
                    if event.key == pygame.K_l:  # 땅굴 파기
                        self.player.start_digging(self.floors)
                    elif event.key == pygame.K_s:  # 아래로 이동
                        self.player.move_down(self.floors)
                    elif event.key == pygame.K_SPACE:  # 점프 (위로 이동)
                        self.player.jump()
                
                # 이름 입력 모드
                elif self.game_state == "name_input":
                    if event.key == pygame.K_RETURN and len(self.player_name) > 0:
                        # 엔터 키: 이름 확정
                        self.add_ranking(self.player_name, self.final_time / 1000)
                        self.game_state = "clear"
                    elif event.key == pygame.K_BACKSPACE:
                        # 백스페이스: 한 글자 삭제
                        self.player_name = self.player_name[:-1]
                    elif event.unicode and len(self.player_name) < 10:
                        # 일반 문자 입력 (최대 10글자)
                        if event.unicode.isprintable():
                            self.player_name += event.unicode
                
                # 게임 재시작
                if event.key == pygame.K_r and self.game_state in ["gameover", "clear"]:
                    self.__init__()
                    
                # 게임 종료
                if event.key == pygame.K_ESCAPE:
                    self.running = False
        
        # 연속 키 입력 처리 (플레이 중일 때만)
        if self.game_state == "playing":
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:  # 왼쪽
                self.player.move(-1, self.floors)
            if keys[pygame.K_d]:  # 오른쪽
                self.player.move(1, self.floors)
    
    def update(self):
        """게임 로직 업데이트"""
        if self.game_state == "playing":
            # 타이머 업데이트
            self.elapsed_time = pygame.time.get_ticks() - self.start_time
            
            # 플레이어 업데이트
            self.player.update(self.floors)
            
            # 몬스터 업데이트
            for monster in self.monsters:
                monster.update()
            
            # 충돌 감지
            self.check_collisions()
            
            # 카메라 업데이트 (플레이어를 따라가도록)
            available_height = SCREEN_HEIGHT - GAME_FIELD_Y
            target_camera_y = self.player.current_floor * FLOOR_HEIGHT - available_height // 3
            max_camera_y = TOTAL_FLOORS * FLOOR_HEIGHT - available_height + GAME_FIELD_Y
            self.camera_y = max(0, min(target_camera_y, max_camera_y))
            
            # 클리어 조건 체크 (지하 30층 = 인덱스 30)
            if self.player.current_floor >= TOTAL_FLOORS - 1:
                self.final_time = self.elapsed_time
                # 랭킹 진입 여부 확인
                if self.check_ranking(self.final_time / 1000):
                    self.is_new_record = True
                    self.game_state = "name_input"
                else:
                    self.is_new_record = False
                    self.game_state = "clear"
    
    def check_collisions(self):
        """충돌 감지"""
        player_rect = self.player.get_rect()
        
        for monster in self.monsters:
            if monster.floor == self.player.current_floor:
                monster_rect = monster.get_rect()
                if player_rect.colliderect(monster_rect):
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
            
            # 화면에 보이는 층만 그리기 (UI 영역 아래)
            if GAME_FIELD_Y - FLOOR_HEIGHT <= y_pos <= SCREEN_HEIGHT:
                # 층 기본 배경 (현대적 디자인)
                if floor_num == 0:
                    # 지상층 - 그라디언트 초록색
                    base_color = GROUND_SURFACE
                    dark_color = GROUND_SURFACE_DARK
                else:
                    # 지하층 - 그라디언트 갈색
                    base_color = GROUND_UNDERGROUND
                    dark_color = GROUND_UNDERGROUND_DARK
                
                # 층 카드 스타일 배경
                floor_rect = pygame.Rect(55, y_pos + 5, SCREEN_WIDTH - 110, FLOOR_HEIGHT - 10)
                
                # 그라디언트 효과
                for i in range(FLOOR_HEIGHT - 10):
                    alpha = i / (FLOOR_HEIGHT - 10)
                    r = int(base_color[0] + (dark_color[0] - base_color[0]) * alpha)
                    g = int(base_color[1] + (dark_color[1] - base_color[1]) * alpha)
                    b = int(base_color[2] + (dark_color[2] - base_color[2]) * alpha)
                    pygame.draw.line(self.screen, (r, g, b), 
                                   (55, y_pos + 5 + i), 
                                   (SCREEN_WIDTH - 55, y_pos + 5 + i))
                
                # 파진 구멍들 그리기 (현대적 스타일)
                for hole_start, hole_end in floor['holes']:
                    hole_width = hole_end - hole_start
                    
                    # 구멍 그림자
                    shadow_rect = pygame.Rect(hole_start + 3, y_pos + 3, hole_width, FLOOR_HEIGHT)
                    if shadow_rect.right > 55 and shadow_rect.left < SCREEN_WIDTH - 55:
                        shadow_surf = pygame.Surface((hole_width, FLOOR_HEIGHT), pygame.SRCALPHA)
                        shadow_surf.fill((0, 0, 0, 100))
                        self.screen.blit(shadow_surf, (hole_start + 3, y_pos + 3))
                    
                    # 구멍 본체 (둥근 모서리)
                    hole_rect = pygame.Rect(hole_start, y_pos, hole_width, FLOOR_HEIGHT)
                    if hole_rect.right > 55 and hole_rect.left < SCREEN_WIDTH - 55:
                        draw_rounded_rect(self.screen, HOLE_COLOR, hole_rect, 10, 3, CARD_BORDER)
                        
                        # 구멍 내부 그라디언트
                        for i in range(FLOOR_HEIGHT - 6):
                            alpha = i / FLOOR_HEIGHT
                            shade = int(23 + 20 * alpha)
                            pygame.draw.line(self.screen, (shade, shade, shade),
                                           (hole_start + 10, y_pos + 3 + i),
                                           (hole_start + hole_width - 10, y_pos + 3 + i))
                
                # 층 카드 테두리
                pygame.draw.rect(self.screen, CARD_BORDER, floor_rect, 2, border_radius=8)
                
                # 층 번호 표시 (카드 스타일)
                if floor_num == 0:
                    floor_label = "지상"
                    label_color = SUCCESS
                    label_width = 38
                else:
                    floor_label = f"B{floor_num}"
                    label_color = TEXT_SECONDARY
                    # 숫자가 두 자리면 박스를 약간 넓게
                    label_width = 38 if floor_num < 10 else 42
                
                # 층 번호 배경 (약간 더 작고 정확한 크기)
                label_bg = pygame.Rect(10, y_pos + FLOOR_HEIGHT // 2 - 12, label_width, 24)
                draw_rounded_rect(self.screen, CARD_BG, label_bg, 5)
                pygame.draw.rect(self.screen, CARD_BORDER, label_bg, 1, border_radius=5)
                
                # 텍스트 렌더링 (더 작은 폰트 사용)
                floor_text = self.font_micro.render(floor_label, True, label_color)
                text_rect = floor_text.get_rect(center=(label_bg.centerx, label_bg.centery))
                self.screen.blit(floor_text, text_rect)
        
        # 몬스터 그리기
        for monster in self.monsters:
            monster_y = monster.y - self.camera_y
            if GAME_FIELD_Y - FLOOR_HEIGHT <= monster_y <= SCREEN_HEIGHT:
                monster.draw(self.screen, self.camera_y)
        
        # 플레이어 그리기
        self.player.draw(self.screen, self.camera_y)
        
        # UI 정보 표시
        self.draw_ui()
        
        # 게임 오버, 이름 입력 또는 클리어 화면
        if self.game_state == "gameover":
            self.draw_gameover()
        elif self.game_state == "name_input":
            self.draw_name_input()
        elif self.game_state == "clear":
            self.draw_clear()
        
        pygame.display.flip()
    
    def draw_ui(self):
        """UI 정보 그리기 - 현대적 카드 디자인"""
        # 상단 UI 배경 (완전 불투명으로 게임 필드 가림)
        pygame.draw.rect(self.screen, BG_DARK, (0, 0, SCREEN_WIDTH, UI_HEIGHT))
        
        # 하단 구분선 (그라디언트 효과)
        gradient_surf = pygame.Surface((SCREEN_WIDTH, 5), pygame.SRCALPHA)
        for i in range(5):
            alpha = int(100 - (i * 20))
            color = CARD_BORDER + (alpha,)
            pygame.draw.line(gradient_surf, color, (0, i), (SCREEN_WIDTH, i))
        self.screen.blit(gradient_surf, (0, UI_HEIGHT - 5))
        
        # 왼쪽 카드: 현재 층 정보
        left_card = pygame.Rect(10, 10, 200, 70)
        draw_rounded_rect(self.screen, CARD_BG, left_card, 10, 2, CARD_BORDER)
        
        if self.player.current_floor == 0:
            floor_display = "지상"
            floor_color = SUCCESS
        else:
            floor_display = f"지하 {self.player.current_floor}층"
            floor_color = PRIMARY
        
        floor_label = self.font_micro.render("현재 위치", True, TEXT_MUTED)
        floor_text = self.font_medium.render(floor_display, True, floor_color)
        goal_text = self.font_micro.render("목표: B30", True, TEXT_SECONDARY)
        
        self.screen.blit(floor_label, (20, 16))
        self.screen.blit(floor_text, (20, 35))
        self.screen.blit(goal_text, (20, 63))
        
        # 중앙 카드: 타이머
        center_card = pygame.Rect(SCREEN_WIDTH // 2 - 100, 10, 200, 70)
        draw_rounded_rect(self.screen, CARD_BG, center_card, 10, 2, WARNING)
        
        # 타이머 아이콘 효과
        time_display = self.format_time(self.elapsed_time)
        timer_label = self.font_micro.render("⏱ TIMER", True, TEXT_MUTED)
        time_text = self.font_medium.render(time_display, True, WARNING)
        
        timer_rect = timer_label.get_rect(center=(SCREEN_WIDTH // 2, 22))
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, 52))
        
        # 글로우 효과
        glow_surf = pygame.Surface((time_text.get_width() + 40, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, WARNING + (30,), (0, 0, time_text.get_width() + 40, 40))
        self.screen.blit(glow_surf, (time_rect.x - 20, time_rect.y - 5))
        
        self.screen.blit(timer_label, timer_rect)
        self.screen.blit(time_text, time_rect)
        
        # 우측 카드: 조작법
        right_card = pygame.Rect(SCREEN_WIDTH - 210, 10, 200, 70)
        draw_rounded_rect(self.screen, CARD_BG, right_card, 10, 2, CARD_BORDER)
        
        controls_label = self.font_micro.render("조작법", True, TEXT_MUTED)
        control_line1 = self.font_micro.render("이동: A D S", True, TEXT_SECONDARY)
        control_line2 = self.font_micro.render("점프: Space", True, TEXT_SECONDARY)
        control_line3 = self.font_micro.render("파기: L", True, TEXT_SECONDARY)
        
        self.screen.blit(controls_label, (SCREEN_WIDTH - 195, 14))
        self.screen.blit(control_line1, (SCREEN_WIDTH - 195, 32))
        self.screen.blit(control_line2, (SCREEN_WIDTH - 195, 48))
        self.screen.blit(control_line3, (SCREEN_WIDTH - 195, 64))
    
    def draw_gameover(self):
        """게임 오버 화면 - 현대적 디자인"""
        # 반투명 그라디언트 배경
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            alpha = int(180 + (y / SCREEN_HEIGHT) * 60)
            pygame.draw.line(overlay, BG_DARKER + (alpha,), (0, y), (SCREEN_WIDTH, y))
        self.screen.blit(overlay, (0, 0))
        
        # 중앙 카드
        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150, 500, 300)
        
        # 카드 그림자
        shadow_rect = (card_rect.x + 8, card_rect.y + 8, card_rect.width, card_rect.height)
        shadow_surf = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 100))
        self.screen.blit(shadow_surf, (shadow_rect[0], shadow_rect[1]))
        
        # 카드 본체
        draw_rounded_rect(self.screen, CARD_BG, card_rect, 20, 3, DANGER)
        
        # GAME OVER 텍스트 (애니메이션 효과)
        pulse = abs(((pygame.time.get_ticks() // 10) % 100) - 50) / 50
        glow_size = int(100 + pulse * 50)
        glow_surf = pygame.Surface((glow_size * 3, glow_size), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, DANGER + (50,), (0, 0, glow_size * 3, glow_size))
        self.screen.blit(glow_surf, (SCREEN_WIDTH // 2 - glow_size * 1.5, SCREEN_HEIGHT // 2 - 100 - glow_size // 2))
        
        gameover_text = self.font_large.render("💀 GAME OVER", True, DANGER)
        text_rect = gameover_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70))
        self.screen.blit(gameover_text, text_rect)
        
        # 구분선
        pygame.draw.line(self.screen, CARD_BORDER, 
                        (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 10),
                        (SCREEN_WIDTH // 2 + 200, SCREEN_HEIGHT // 2 - 10), 2)
        
        # 재시작 안내
        restart_label = self.font_small.render("다시 도전하기", True, TEXT_MUTED)
        restart_text = self.font_medium.render("R 키", True, PRIMARY)
        
        restart_label_rect = restart_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        
        self.screen.blit(restart_label, restart_label_rect)
        self.screen.blit(restart_text, restart_rect)
    
    def draw_name_input(self):
        """이름 입력 화면 - 현대적 디자인"""
        # 반투명 그라디언트 배경
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            alpha = int(200 + (y / SCREEN_HEIGHT) * 40)
            pygame.draw.line(overlay, BG_DARKER + (alpha,), (0, y), (SCREEN_WIDTH, y))
        self.screen.blit(overlay, (0, 0))
        
        # 중앙 카드
        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - 280, SCREEN_HEIGHT // 2 - 180, 560, 360)
        
        # 카드 그림자
        shadow_rect = (card_rect.x + 10, card_rect.y + 10, card_rect.width, card_rect.height)
        shadow_surf = pygame.Surface((card_rect.width, card_rect.height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 120))
        self.screen.blit(shadow_surf, (shadow_rect[0], shadow_rect[1]))
        
        # 카드 본체
        draw_rounded_rect(self.screen, CARD_BG, card_rect, 25, 3, WARNING)
        
        # 축하 메시지 (애니메이션 효과)
        pulse = abs(((pygame.time.get_ticks() // 10) % 100) - 50) / 50
        glow_size = int(120 + pulse * 60)
        glow_surf = pygame.Surface((glow_size * 2, glow_size), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, WARNING + (60,), (0, 0, glow_size * 2, glow_size))
        self.screen.blit(glow_surf, (SCREEN_WIDTH // 2 - glow_size, SCREEN_HEIGHT // 2 - 140 - glow_size // 2))
        
        congrats_text = self.font_large.render("🏆 신기록! 🏆", True, WARNING)
        congrats_rect = congrats_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
        self.screen.blit(congrats_text, congrats_rect)
        
        # 클리어 시간
        time_display = self.format_time(self.final_time)
        time_label = self.font_small.render("클리어 타임", True, TEXT_MUTED)
        time_text = self.font_medium.render(time_display, True, PRIMARY)
        
        time_label_rect = time_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60))
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        
        self.screen.blit(time_label, time_label_rect)
        self.screen.blit(time_text, time_rect)
        
        # 구분선
        pygame.draw.line(self.screen, CARD_BORDER,
                        (SCREEN_WIDTH // 2 - 230, SCREEN_HEIGHT // 2 + 5),
                        (SCREEN_WIDTH // 2 + 230, SCREEN_HEIGHT // 2 + 5), 2)
        
        # 이름 입력 안내
        prompt_text = self.font_small.render("명예의 전당에 새길 이름 (최대 10글자)", True, TEXT_SECONDARY)
        prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 35))
        self.screen.blit(prompt_text, prompt_rect)
        
        # 입력 박스 (현대적 스타일)
        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 70, 360, 60)
        draw_rounded_rect(self.screen, BG_DARK, input_box, 12, 3, PRIMARY)
        
        # 입력된 이름 표시
        cursor_blink = (pygame.time.get_ticks() // 500) % 2
        display_name = self.player_name + ("_" if cursor_blink else "")
        name_text = self.font_medium.render(display_name, True, TEXT_PRIMARY)
        name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(name_text, name_rect)
        
        # 확인 안내
        confirm_text = self.font_small.render("Enter 키를 눌러 등록", True, SUCCESS)
        confirm_rect = confirm_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self.screen.blit(confirm_text, confirm_rect)
    
    def draw_clear(self):
        """클리어 화면 - 현대적 디자인"""
        # 반투명 그라디언트 배경
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            alpha = int(200 + (y / SCREEN_HEIGHT) * 40)
            pygame.draw.line(overlay, BG_DARKER + (alpha,), (0, y), (SCREEN_WIDTH, y))
        self.screen.blit(overlay, (0, 0))
        
        # CLEAR 텍스트 (팡파레 효과)
        time_offset = pygame.time.get_ticks() // 100
        color_r = abs(int(127 * (1 + pygame.math.Vector2(1, 0).rotate(time_offset * 10).x)))
        color_g = abs(int(127 * (1 + pygame.math.Vector2(1, 0).rotate(time_offset * 15).y)))
        color_b = 255
        
        # 글로우 효과
        pulse = abs(((pygame.time.get_ticks() // 10) % 100) - 50) / 50
        glow_size = int(150 + pulse * 80)
        glow_surf = pygame.Surface((glow_size * 2, glow_size), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (color_r, color_g, color_b, 80), (0, 0, glow_size * 2, glow_size))
        self.screen.blit(glow_surf, (SCREEN_WIDTH // 2 - glow_size, 60 - glow_size // 2))
        
        clear_text = self.font_large.render("★ CLEAR ★", True, (color_r, color_g, color_b))
        text_rect = clear_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(clear_text, text_rect)
        
        # 클리어 시간 카드
        time_card = pygame.Rect(SCREEN_WIDTH // 2 - 150, 130, 300, 70)
        draw_rounded_rect(self.screen, CARD_BG, time_card, 15, 3, SUCCESS)
        
        time_label = self.font_small.render("클리어 타임", True, TEXT_MUTED)
        time_display = self.format_time(self.final_time)
        time_text = self.font_medium.render(time_display, True, SUCCESS)
        
        time_label_rect = time_label.get_rect(center=(SCREEN_WIDTH // 2, 145))
        time_rect = time_text.get_rect(center=(SCREEN_WIDTH // 2, 175))
        
        self.screen.blit(time_label, time_label_rect)
        self.screen.blit(time_text, time_rect)
        
        # 랭킹 카드
        ranking_card = pygame.Rect(SCREEN_WIDTH // 2 - 280, 230, 560, 220)
        draw_rounded_rect(self.screen, CARD_BG, ranking_card, 20, 3, WARNING)
        
        # 랭킹 제목
        ranking_title = self.font_medium.render("🏆 명예의 전당 🏆", True, WARNING)
        ranking_title_rect = ranking_title.get_rect(center=(SCREEN_WIDTH // 2, 260))
        self.screen.blit(ranking_title, ranking_title_rect)
        
        # 구분선
        pygame.draw.line(self.screen, CARD_BORDER,
                        (SCREEN_WIDTH // 2 - 240, 290),
                        (SCREEN_WIDTH // 2 + 240, 290), 2)
        
        # 순위 표시
        medals = ["🥇", "🥈", "🥉"]
        medal_colors = [WARNING, (192, 192, 192), (205, 127, 50)]  # 금, 은, 동
        
        for i, record in enumerate(self.rankings[:3]):
            y_pos = 315 + i * 45
            
            # 순위 배경
            rank_bg = pygame.Rect(SCREEN_WIDTH // 2 - 260, y_pos - 5, 520, 35)
            if i % 2 == 0:
                draw_rounded_rect(self.screen, BG_DARK, rank_bg, 8)
            
            # 메달과 순위
            medal_text = self.font_medium.render(f"{medals[i]} {i+1}위", True, medal_colors[i])
            self.screen.blit(medal_text, (SCREEN_WIDTH // 2 - 240, y_pos))
            
            # 이름
            name_text = self.font_small.render(record['name'], True, TEXT_PRIMARY)
            self.screen.blit(name_text, (SCREEN_WIDTH // 2 - 100, y_pos + 5))
            
            # 시간
            time_str = self.format_time(record['time'] * 1000)
            time_render = self.font_small.render(time_str, True, PRIMARY)
            time_render_rect = time_render.get_rect(right=SCREEN_WIDTH // 2 + 240, centery=y_pos + 12)
            self.screen.blit(time_render, time_render_rect)
        
        # 재시작 버튼 스타일
        restart_card = pygame.Rect(SCREEN_WIDTH // 2 - 100, 480, 200, 50)
        draw_rounded_rect(self.screen, CARD_BG, restart_card, 12, 3, PRIMARY)
        
        restart_text = self.font_medium.render("R 키로 재시작", True, PRIMARY)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, 505))
        self.screen.blit(restart_text, restart_rect)
    
    def run(self):
        """게임 메인 루프"""
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

# 게임 실행
if __name__ == "__main__":
    game = Game()
    game.run()

