import pip
pip.main(["install", "pygame"])

import pygame
import sys
from enum import Enum
import time
import math
import random

class Status(Enum):
    END = 1
    TURN_1 = 2
    TURN_2 = 3
    WAITING_1 = 4
    WAITING_2 = 5
    BEFORE_ATTACK_1 = 6
    BEFORE_ATTACK_2 = 7
    DEFENDING_1 = 8
    DEFENDING_2 = 9
    ATTACK_1 = 10
    ATTACK_2 = 11

class Hand:
    def __init__(self, screen, direction, foldedList, pos, playerNum):
        self.screen = screen
        # direction == 0 <- 왼손 / 1 <- 오른손
        self.direction = direction
        foldedHeight = [foldedList[i] * 60 + 60 for i in range(4)] # 접힌 손가락: 60px, 핀 손가락: 120px
        # pos: 손바닥의 왼쪽 아래 꼭짓점 기준
        self.pos = pos
        self.playerNum = playerNum

        self.finger_width = 40
        self.spacing = 40 / 3
        self.angle = 35

        self.Palm = pygame.Rect(self.pos[0], self.pos[1] - 200, 200, 125)


        self.Thumb = pygame.Rect(0, 0, 80, 60)
        if self.direction == 1:
            self.Thumb.bottomright = self.Palm.bottomleft
        elif self.direction == 0:
            self.Thumb.bottomleft = self.Palm.bottomright
        
        self.Fingers = [pygame.Rect(0, 0, self.finger_width, foldedHeight[i]) for i in range(4)]
        
        for i, finger in enumerate(self.Fingers):
            x = self.Palm.left + i * (self.finger_width + self.spacing)
            y = self.Palm.top
            finger.bottomleft = (x, y)
            
    # 손을 화면에 그리는 함수
    def drawHand(self):
        if self.playerNum == 0:
            color = 'yellow'
        elif self.playerNum == 1:
            color = 'white'
        else:
            color = 'red'
        pygame.draw.rect(self.screen, color, self.Palm)
        pygame.draw.rect(self.screen, color, self.Thumb)
        for finger in self.Fingers:
            pygame.draw.rect(self.screen, color, finger)

class Player():
    def __init__(self, playerNum):
        self.playerNum = playerNum
        self.hp = 100
        self.mp = 0
        
        self.font = pygame.font.Font("assets/neodgm.ttf", 24)
            
        character_size = (144, 144) 

        if playerNum == 1:
            default_p = pygame.image.load("assets/p1_default.png")
            default_p = pygame.transform.scale(default_p, character_size)
            self.p_size = list(default_p.get_size())
            self.p_pos = [328, 200]
            centerX = (328 + 144 // 2) 
        else:
            default_p = pygame.image.load("assets/p2_default.png")
            default_p = pygame.transform.scale(default_p, character_size)
            self.p_size = list(default_p.get_size())
            self.p_pos = [1128, 200]
            centerX = (1128 + 144 // 2) 

        self.current_p = default_p

        bar_height = 20
        max_bar_width = 200 
        
        self.border_thickness = 4

        self.hpBar_frame = pygame.Rect(0, 0, max_bar_width, bar_height) 
        self.mpBar_frame = pygame.Rect(0, 0, max_bar_width, bar_height)
        
        self.hpBar_fill = pygame.Rect(0, 0, self.hp * 2, bar_height) 
        self.mpBar_fill = pygame.Rect(0, 0, self.mp * 2, bar_height)
        
        self.hpBar_frame.center = (centerX, 100)
        self.mpBar_frame.center = (centerX, 140)

        self.hpBar_fill.topleft = self.hpBar_frame.topleft
        self.mpBar_fill.topleft = self.mpBar_frame.topleft
    
    def drawCharacter(self, screen):
        screen.blit(self.current_p, self.p_pos)
        
        pygame.draw.rect(screen, (255, 255, 255), self.hpBar_frame, self.border_thickness)

        fill_left = self.hpBar_frame.left + self.border_thickness
        fill_top = self.hpBar_frame.top + self.border_thickness
        fill_width = (self.hp * 2) - (self.border_thickness * 2)
        fill_height = self.hpBar_frame.height - (self.border_thickness * 2)

        if fill_width < 0: fill_width = 0
        if fill_height < 0: fill_height = 0

        current_hp_fill_rect = pygame.Rect(fill_left, fill_top, fill_width, fill_height)
        pygame.draw.rect(screen, 'green', current_hp_fill_rect) 
        
        pygame.draw.rect(screen, (255, 255, 255), self.mpBar_frame, self.border_thickness)

        mp_fill_left = self.mpBar_frame.left + self.border_thickness
        mp_fill_top = self.mpBar_frame.top + self.border_thickness
        mp_fill_width = (self.mp * 2) - (self.border_thickness * 2)
        mp_fill_height = self.mpBar_frame.height - (self.border_thickness * 2)

        if mp_fill_width < 0: mp_fill_width = 0
        if mp_fill_height < 0: mp_fill_height = 0

        current_mp_fill_rect = pygame.Rect(mp_fill_left, mp_fill_top, mp_fill_width, mp_fill_height)
        pygame.draw.rect(screen, 'yellow', current_mp_fill_rect)

        if self.font:
            hp_label_surface = self.font.render("HP", True, (255, 255, 255)) 
            hp_label_rect = hp_label_surface.get_rect(
                midright=(self.hpBar_frame.left - 10, self.hpBar_frame.centery)
            )
            screen.blit(hp_label_surface, hp_label_rect)

            mp_label_surface = self.font.render("MP", True, (255, 255, 255)) 
            mp_label_rect = mp_label_surface.get_rect(
                midright=(self.mpBar_frame.left - 10, self.mpBar_frame.centery)
            )
            screen.blit(mp_label_surface, mp_label_rect)

class Skill: # 동작이 모여서 스킬이 돼요
    def __init__(self, motionList, skillType, damage, image_p1, image_p2):
        self.motionList = motionList
        self.skillType = skillType
        self.damage = damage
        self.image_p1 = pygame.image.load(image_p1)
        self.image_p2 = pygame.image.load(image_p2)
    
    def drawSkill(self, screen, player, tick):
        skill_image = self.image_p1 if player.playerNum == 1 else self.image_p2
        
        if self.skillType == 'attack' or self.skillType == 'ultimate':
            skill_image = pygame.transform.scale(skill_image, (32 * 20, 32 * 5))
            
            if (tick // 5) % 2 == 0: # 5틱마다 바꾸기
                skill_image = pygame.transform.flip(skill_image, False, True)
        else:
            skill_image = pygame.transform.scale(skill_image, (32 * 5, 32 * 5))
        
        
        skill_rect = skill_image.get_rect()
        
        character_rect = pygame.Rect(
            player.p_pos[0], 
            player.p_pos[1], 
            player.p_size[0], 
            player.p_size[1]
        )
        
        if player.playerNum == 1:
            pos = (character_rect.midright[0] - 50, character_rect.midright[1])
            skill_rect.midleft = pos
        else:
            pos = (character_rect.midleft[0] + 50, character_rect.midleft[1])
            skill_rect.midright = pos
            
        screen.blit(skill_image, skill_rect)
        
def drawVirtualHand(playerNum, isWaiting=False, events=None):
    leftFolded = [1, 1, 1, 1]
    rightFolded = [1, 1, 1, 1]
    fingerReturn = False
    fingerSet = set()
    
    if not isWaiting:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_1]:
            leftFolded[0] = 0
            fingerSet.add(1)
        if keys[pygame.K_2]:
            leftFolded[1] = 0
            fingerSet.add(2)
        if keys[pygame.K_3]:
            leftFolded[2] = 0
            fingerSet.add(3)
        if keys[pygame.K_4]:
            leftFolded[3] = 0
            fingerSet.add(4)
        if keys[pygame.K_7]:
            rightFolded[0] = 0
            fingerSet.add(7)
        if keys[pygame.K_8]:
            rightFolded[1] = 0
            fingerSet.add(8)
        if keys[pygame.K_9]:
            rightFolded[2] = 0
            fingerSet.add(9)
        if keys[pygame.K_0]:
            rightFolded[3] = 0
            fingerSet.add(0)
        if events is None:
            events = []
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    fingerReturn = True # 모션 발동
                if e.key == pygame.K_TAB:
                    fingerSet = 'COMPLETE'
                    fingerReturn = True

    leftHand = Hand(screen, direction=0, foldedList=leftFolded, pos=(300, 800), playerNum=playerNum)
    rightHand = Hand(screen, direction=1, foldedList=rightFolded, pos=(1100, 800), playerNum=playerNum)

    leftHand.drawHand()
    rightHand.drawHand()

    if fingerReturn:
        return fingerSet

def game_off(): # 게임 종료
    pygame.quit()
    sys.exit()

def waiting(seconds):
    end_time = time.time() + seconds
    while time.time() < end_time:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_off()
                return
        pygame.display.flip()
        clock.tick(60)

# 동작 모음
motions = {
    '피스 사인': {8, 2, 9, 3},
    'HYPER TEXT': {9, 2, 4, 7},
    '왼손 주먹': {1, 2, 3, 4},
    '오른손 주먹': {7, 8, 9, 0},
    '가위': {1, 2, 9, 0},
    '바위': {1, 2, 3, 4, 7, 8, 9, 0},
    '보자기': set(),
    '오른손 가리키기': {1, 2, 3, 8, 9, 0, 4},
    '왼손 가리키기': {1, 2, 3, 8, 9, 0, 7}
    
}

skills = {
    '손 풀기': Skill(['왼손 주먹', '오른손 주먹'], skillType='attack', damage=30, image_p1="assets/p1_common_attack.png", image_p2="assets/p2_common_attack.png"),
    '가위바위보': Skill(['가위', '바위', '보자기'], skillType='attack', damage=40, image_p1="assets/p1_common_attack.png", image_p2="assets/p2_common_attack.png"),
    '삿대질': Skill(['왼손 가리키기', '오른손 가리키기', '가위'], skillType='attack', damage=40, image_p1="assets/p1_common_attack.png", image_p2="assets/p2_common_attack.png"),
    '술식전개': Skill(['가위', '보자기', '가위', '피스 사인', '바위'], skillType='attack', damage=70, image_p1="assets/p1_common_attack.png", image_p2="assets/p2_common_attack.png"),
    '테스트': Skill(['보자기'], skillType='attack', damage=100, image_p1="assets/p1_common_attack.png", image_p2="assets/p2_common_attack.png"),
    
    '막기': Skill([], skillType='defense', damage=5, image_p1="assets/p1_sheild.png", image_p2="assets/p2_sheild.png"),
    
    
    '궁극기': Skill(['HYPER TEXT'], skillType='ultimate', damage=60, image_p1="assets/p1_laser.png", image_p2="assets/p2_laser.png")
}

clock = pygame.time.Clock()
pygame.init()

WIDTH = 1600
HEIGHT = WIDTH * 9 / 16
screen = pygame.display.set_mode((WIDTH, HEIGHT))
main = True
ingame = True
status = Status.WAITING_1
isAttack = True

attack_skill_status = ''
defending_skill_status = ''
attack_damage = 0
defending_damage = 0

motion_font = pygame.font.Font('assets/neodgm.ttf', 30)
motionTimer = 0
motionTimerProgress = pygame.Rect(0, 50, 240, 30)
motionList = [] # 모션이 담길 리스트
prevFingerSet = None
character_size = (144, 144) # 기본 캐릭터 사이즈(재사용 용도)

turnTimer = 600 # 턴 타이머(10초)
turnTimerProgress = pygame.Rect(0, HEIGHT - 100, WIDTH, 60)

main_font = pygame.font.Font('assets/neodgm.ttf', 80)
sub_font = pygame.font.Font('assets/neodgm.ttf', 40)

p1 = Player(1)
p2 = Player(2)
 

while main:
    while ingame:
        while status == Status.WAITING_1 or status == Status.WAITING_2:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    game_off()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        if status == Status.WAITING_1:
                            if attack_skill_status == '': # 공격 실패 시/초기
                                status = Status.TURN_1
                            else: # 공격 성공
                                status = Status.DEFENDING_1
                        elif status == Status.WAITING_2:
                            if attack_skill_status == '': # 공격 실패 시/초기
                                status = Status.TURN_2
                            else: # 공격 성공
                                status = Status.DEFENDING_2
                        break 
                    
            if status != Status.WAITING_1 and status != Status.WAITING_2:
                break

            screen.fill((0, 0, 0))
            player_num = 1 if status == Status.WAITING_1 else 2

            drawVirtualHand(player_num, True, events)
            p1.drawCharacter(screen)
            p2.drawCharacter(screen)
            
            # 화면 약간 어둡게 만들기
            overlay_size = (WIDTH, HEIGHT)
            overlay_surface = pygame.Surface(overlay_size, pygame.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 200))
            screen.blit(overlay_surface, (0, 0))

            if isAttack:
                gongsu = '공격' # 공(격)/수(비) ^^
            else:
                gongsu = '방어'

            main_text = main_font.render(f"플레이어 {player_num} 입력 대기 중...", False, "white")
            sub_text = sub_font.render(f"Tab을 눌러 {gongsu} 시작하기", False, "white")

            main_text_rect = main_text.get_rect()
            sub_text_rect = sub_text.get_rect()

            main_text_rect.center = (WIDTH // 2, HEIGHT // 2 - 50)
            sub_text_rect.center = (WIDTH // 2, HEIGHT // 2 + 50)

            screen.blit(main_text, main_text_rect)
            screen.blit(sub_text, sub_text_rect)
            
            pygame.display.flip()
            clock.tick(60)

        while status == Status.BEFORE_ATTACK_1 or status == Status.BEFORE_ATTACK_2:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    game_off()

            screen.fill((0, 0, 0))
            
            player_num = 1 if status == Status.BEFORE_ATTACK_1 else 2
            p1.drawCharacter(screen)
            p2.drawCharacter(screen)
            
            drawVirtualHand(player_num, False, events)
            
            # 화면 약간 어둡게 만들기
            overlay_size = (WIDTH, HEIGHT)
            overlay_surface = pygame.Surface(overlay_size, pygame.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 200))
            screen.blit(overlay_surface, (0, 0))
            
            if attack_skill_status != '':
                main_text = main_font.render(f"{attack_skill_status}", False, "white")
                sub_text = sub_font.render(f"플레이어 {player_num} 공격 성공!", False, "white")
                main_text_rect = main_text.get_rect()
                sub_text_rect = sub_text.get_rect()
                
                main_text_rect.center = (WIDTH // 2, HEIGHT // 2 - 50)
                sub_text_rect.center = (WIDTH // 2, HEIGHT // 2 + 50)
                
                screen.blit(main_text, main_text_rect)
                screen.blit(sub_text, sub_text_rect)
                isAttack = False
                
            else:
                main_text = main_font.render(f"플레이어 {player_num} 공격 실패!", False, "white")
                main_text_rect = main_text.get_rect()
                main_text_rect.center = (WIDTH // 2, HEIGHT // 2 - 50)
                screen.blit(main_text, main_text_rect)
                
                isAttack = True
                attack_skill_status = ''
                
            status = Status.WAITING_2 if status == Status.BEFORE_ATTACK_1 else Status.WAITING_1
            pygame.display.flip()
            clock.tick(60)
            # wait 3 seconds while ignoring key inputs, but still processing QUIT
            waiting(3)
            
            if player_num == 2:
                if (p1.hp <= 0 or p2.hp <= 0) and attack_skill_status == '':
                    status = status.END
                    break

        while status == Status.DEFENDING_1 or status == Status.DEFENDING_2:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    game_off()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F12:
                        if status == Status.DEFENDING_2:
                            status = Status.ATTACK_1
                        else:
                            status = Status.ATTACK_2
                        motionTimer = 0
                        motionList = []
                        turnTimer = 600
                    
            screen.fill((0, 0, 0))

            # 유저가 스페이스바 누르면 값 들어옴
            fingerSet = drawVirtualHand(player_num, False, events)
            
            # 모션 사전에 있으면 모션 목록에 추가함
            if fingerSet is not None and fingerSet != prevFingerSet:
                print(fingerSet)
                if fingerSet == 'COMPLETE':
                    motionTimer = 0
                else:
                    for k, v in motions.items():
                        if v == fingerSet:
                            motionList.append(k)
                            motionTimer = 120  # 2초 동안 모션이 유효함
                            break

            prevFingerSet = fingerSet # 중복 입력 방지

            if motionTimer > 0: 
                text = motion_font.render(motionList[-1], False, "white")
                screen.blit(text, (0, 0))
                motionTimer -= 1
                motionTimerProgress.width = (motionTimer / 120) * 240
                pygame.draw.rect(screen, (255, 255, 255), motionTimerProgress)
            else:
                if list(reversed(skills[attack_skill_status].motionList)) == motionList and skills[attack_skill_status].skillType == 'attack': # 스킬 완성 시
                    motionTimer = 0
                    damage_multiple = turnTimer / 600 * 0.3 # 방어력 계산 식: 방어력(damage) * (남은 초 / 10초) * 0.3의 올림
                    damage_multiple = 0.1 if damage_multiple < 0.1 else damage_multiple # 최소 방어력 배율: 0.1
                    defending_damage = math.ceil(skills[attack_skill_status].damage * damage_multiple) # 더 빨리 입력할수록 더 많은 방어력
                    print("방어 성공")
                    print("방어력: ", defending_damage)
                    print("방어력 배율: ", damage_multiple)
                    defending_skill_status = '막기'
                    
                    if status == Status.DEFENDING_2:
                        status = Status.ATTACK_1
                    else:
                        status = Status.ATTACK_2
                            
                    motionTimer = 0
                    motionList = []
                    turnTimer = 600
                    break
                motionList = []
            
            if turnTimer > 0:
                turnTimer -= 1
                turnTimerProgress.width = (turnTimer / 600) * WIDTH
                pygame.draw.rect(screen, (255, 255, 255), turnTimerProgress)
            else:
                if status == Status.DEFENDING_2:
                    status = Status.ATTACK_1
                else:
                    status = Status.ATTACK_2
                motionTimer = 0
                motionList = []

                turnTimer = 600
            

            p1.drawCharacter(screen)
            p2.drawCharacter(screen)

            pygame.display.flip()
            clock.tick(60)
            
        while status == Status.ATTACK_1 or status == Status.ATTACK_2:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    game_off()
            player_num = 1 if status == Status.ATTACK_1 else 2
            
            
            hit_damage = attack_damage - defending_damage
            if hit_damage <= 0: hit_damage = 0
            print("피격 데미지:", hit_damage)
            print("공격, 방어: ", attack_damage, ",", defending_damage)
            
            if player_num == 1:
                target_damage = p2.hp - hit_damage
                before_hp = p2.hp
                before_mp = p1.mp
            else:
                target_damage = p1.hp - hit_damage
                before_hp = p1.hp
                before_mp = p2.mp
            
            
            now_damage = 0
            tick_count = 0 # 애니메이션 위한 틱카운트
            tick_damage = hit_damage / 180 # 애니메이션 틱 당 데미지(3초 동안 할 거라 180으로 나눔)
            if attack_skill_status != '궁극기':
                mp_to_fill = skills[attack_skill_status].damage # 마나는 공격력만큼 참
                tick_damage = hit_damage / 180 # 애니메이션 틱 당 데미지(3초 동안 할 거라 180으로 나눔)
            else:
                mp_to_fill = -100
                tick_damage = hit_damage / 300 # 궁극기는 5초
                
            if before_mp + mp_to_fill >= 100:
                mp_to_fill = 100 - before_mp
            
            mp_to_fill_tick = mp_to_fill / 180
            
            
            while True: # 공격 애니메이션 루프
                events = pygame.event.get()
                for event in events:
                    if event.type == pygame.QUIT:
                        game_off()
                screen.fill((0, 0, 0))
                
                if attack_skill_status == '궁극기':
                    drawVirtualHand(0, False, events)
                else:
                    drawVirtualHand(player_num, False, events)
                    
                now_damage += tick_damage
                tick_count += 1
                
                if player_num == 1:
                    p2.hp -= tick_damage
                    p1.mp += mp_to_fill_tick
                else:
                    p1.hp -= tick_damage
                    p2.mp += mp_to_fill_tick
                
                p1.drawCharacter(screen)
                p2.drawCharacter(screen)
                
                target_player = p2 if player_num == 1 else p1
                damage_display = int(now_damage)
                
                if damage_display > 0:
                    damage_text = motion_font.render(f"-{damage_display}", True, (255, 0, 0))
                    damage_rect = damage_text.get_rect()
                    damage_rect.midbottom = (target_player.hpBar_frame.centerx, target_player.hpBar_frame.top - 5)
                    screen.blit(damage_text, damage_rect)
                skills[attack_skill_status].drawSkill(screen, p1 if player_num == 1 else p2, tick_count)
                
                if defending_skill_status:
                    skills[defending_skill_status].drawSkill(screen, p2 if player_num == 1 else p1, tick_count)
                
                screen_copy = screen.copy()
                if attack_skill_status != '궁극기':
                    shake_intensity = 1
                else:
                    shake_intensity = 20
                offset_x = random.randint(-shake_intensity, shake_intensity)
                offset_y = random.randint(-shake_intensity, shake_intensity)
                
                screen.fill((0, 0, 0))
                screen.blit(screen_copy, (offset_x, offset_y))
                
                pygame.display.flip()
                clock.tick(60)
                
                if now_damage >= hit_damage:
                    break
            
            # 소수점 오류 고려해서 hit damage, mp_to_fill로 직접 계산
            if player_num == 1:
                p2.hp = before_hp - hit_damage
                p1.mp = before_mp + mp_to_fill
            else:
                p1.hp = before_hp - hit_damage
                p2.mp = before_mp + mp_to_fill
                # p2 차례에서만 게임이 끝나는 이유:
                # p1 차례에서 게임이 끝나면, p1은 먼저 시작했기 때문에 p2보다 한 번 더 공격한 셈.
                # 따라서 p1이 p2의 hp를 0으로 만들더라도, p2의 공격을 마치고 게임을 끝내야 공정.
                if p1.hp <= 0 or p2.hp <= 0:
                    status = status.END
                    break
            
                
            attack_damage = 0
            defending_damage = 0
            hit_damage = 0
            
            attack_skill_status = ''
            defending_skill_status = ''
            
            status = Status.WAITING_2 if status == Status.ATTACK_1 else Status.WAITING_1
            isAttack = True
            
            screen.fill((0, 0, 0))
            pygame.display.flip()
            clock.tick(60)

        while status == Status.TURN_1 or status == Status.TURN_2:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    game_off()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F12:
                        if status == Status.TURN_1:
                            status = Status.BEFORE_ATTACK_1
                        else:
                            status = Status.BEFORE_ATTACK_2
                        isAttack = True # 공수교대
                        motionTimer = 0
                        motionList = []
                        turnTimer = 600
                    
            
            screen.fill((0, 0, 0))

            # 유저가 스페이스바 누르면 값 들어옴
            fingerSet = drawVirtualHand(player_num, False, events)
            
            # 모션 사전에 있으면 모션 목록에 추가함
            if fingerSet is not None and fingerSet != prevFingerSet:
                print(fingerSet)
                if fingerSet == 'COMPLETE':
                    motionTimer = 0
                else:
                    for k, v in motions.items():
                        if v == fingerSet:
                            motionList.append(k)
                            motionTimer = 120  # 2초 동안 모션이 유효함
                            break

            prevFingerSet = fingerSet # 중복 입력 방지

            if status == Status.TURN_1:
                mp = p1.mp
            else:
                mp = p2.mp

            if motionTimer > 0: 
                text = motion_font.render(motionList[-1], False, "white")
                screen.blit(text, (0, 0))
                motionTimer -= 1
                motionTimerProgress.width = (motionTimer / 120) * 240
                pygame.draw.rect(screen, (255, 255, 255), motionTimerProgress)
            else:
                for k, v in skills.items():
                    if v.motionList == motionList and (v.skillType == 'attack' or (v.skillType == 'ultimate' and mp == 100)): # 스킬 완성 시
                        if v.skillType == 'attack': # 일반 스킬
                            damage_multiple = turnTimer / 600 # 데미지 계산 식: 데미지 * (남은 초 / 10초)의 올림
                            damage_multiple = 0.3 if damage_multiple < 0.3 else damage_multiple # 최소 데미지 배율: 0.3
                            attack_damage = math.ceil(v.damage * damage_multiple) # 더 빨리 입력할수록 더 많은 데미지
                            print("스킬 발동: ", k)
                            print("데미지: ", attack_damage)
                            print("데미지 배율: ", damage_multiple)
                        else: # 궁극기
                            attack_damage = v.damage # 궁극기 사용시 무조건 최대 데미지
                            print("스킬 발동: ", k)
                            print("데미지: ", attack_damage)
                        
                        motionTimer = 0
                        attack_skill_status = k
                        
                        if status == Status.TURN_1:
                            if attack_skill_status == '궁극기': # 궁극기 사용 시 방어 기회 없음
                                status = Status.ATTACK_1
                            else:
                                status = Status.BEFORE_ATTACK_1
            
                        else:
                            if attack_skill_status == '궁극기': # 궁극기 사용 시 방어 기회 없음
                                status = Status.ATTACK_2
                            else:
                                status = Status.BEFORE_ATTACK_2
                                
                        motionTimer = 0
                        motionList = []
                        turnTimer = 600
                        break
                motionList = []
            
            if turnTimer > 0:
                turnTimer -= 1
                turnTimerProgress.width = (turnTimer / 600) * WIDTH
                pygame.draw.rect(screen, (255, 255, 255), turnTimerProgress)
            else:
                if status == Status.TURN_1:
                    status = Status.BEFORE_ATTACK_1
                else:
                    status = Status.BEFORE_ATTACK_2
                motionTimer = 0
                motionList = []

                turnTimer = 600
            

            p1.drawCharacter(screen)
            p2.drawCharacter(screen)

            pygame.display.flip()
            clock.tick(60)

        while status == Status.END:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    game_off()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        status = Status.WAITING_1
                        isAttack = True

                        attack_skill_status = ''
                        defending_skill_status = ''
                        attack_damage = 0
                        defending_damage = 0
                        p1 = Player(1)
                        p2 = Player(2)
                        break 
                    
            screen.fill((0, 0, 0))
            drawVirtualHand(1, True, events)
            p1.drawCharacter(screen)
            p2.drawCharacter(screen)
            
            # 화면 약간 어둡게 만들기
            overlay_size = (WIDTH, HEIGHT)
            overlay_surface = pygame.Surface(overlay_size, pygame.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 200))
            screen.blit(overlay_surface, (0, 0))

            player1_damage = 100 - p2.hp
            player2_damage = 100 - p1.hp
            draw = False
            
            if player1_damage == player2_damage:
                draw = True
            win_player = 1 if player1_damage > player2_damage else 2
            
            if draw:
                main_text = main_font.render(f"무승부", False, "white")
            else:
                main_text = main_font.render(f"플레이어 {win_player} 승리!", False, "white")
            sub_text1 = sub_font.render("입힌 데미지", False, "white")
            sub_text2 = sub_font.render(f"플레이어 1: {player1_damage}             플레이어 2: {player2_damage}", False, "white")
            sub_text3 = sub_font.render("Enter를 눌러 다시 하기", False, "white")
            

            main_text_rect = main_text.get_rect()
            sub_text_rect1 = sub_text1.get_rect()
            sub_text_rect2 = sub_text2.get_rect()
            sub_text_rect3 = sub_text3.get_rect()
            
            main_text_rect.center = (WIDTH // 2, HEIGHT // 2 - 50)
            sub_text_rect1.center = (WIDTH // 2, HEIGHT // 2 + 50)
            sub_text_rect2.center = (WIDTH // 2, HEIGHT // 2 + 100)
            sub_text_rect3.center = (WIDTH // 2, HEIGHT // 2 + 200)

            screen.blit(main_text, main_text_rect)
            screen.blit(sub_text1, sub_text_rect1)
            screen.blit(sub_text2, sub_text_rect2)
            screen.blit(sub_text3, sub_text_rect3)
            
            pygame.display.flip()
            clock.tick(60)
            
    ingame = False
    main = False
