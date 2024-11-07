import pygame
import random
import sys
import math
import os

# 初始化Pygame
pygame.init()

# 设置颜色
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# 设置游戏窗口
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BLOCK_SIZE = 20

# 加载图像
ASSETS_DIR = 'assets'
SUNFLOWER_IMG = pygame.image.load(os.path.join(ASSETS_DIR, 'sunflower.png'))
DRAGONFLY_IMG = pygame.image.load(os.path.join(ASSETS_DIR, 'dragonfly.png'))

# 滑块设置
SLIDER_WIDTH = 200
SLIDER_HEIGHT = 10
SLIDER_X = WINDOW_WIDTH - SLIDER_WIDTH - 20
SLIDER_Y = 20
SLIDER_KNOB_SIZE = 20

# 创建窗口
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('贪吃蛇游戏')

# 速度滑块类
class SpeedSlider:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob = pygame.Rect(x, y - height/2, SLIDER_KNOB_SIZE, SLIDER_KNOB_SIZE)
        self.min_speed = 0.001  # 1毫秒
        self.max_speed = 1.0    # 1秒
        self.dragging = False
        self.value = 0.2        # 默认0.2秒

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.knob.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.knob.centerx = max(self.rect.left, min(event.pos[0], self.rect.right))
            self.update_value()

    def update_value(self):
        # 计算滑块位置对应的速度值（使用对数刻度）
        position_ratio = (self.knob.centerx - self.rect.left) / self.rect.width
        # 使用对数插值来使速度变化更平滑
        log_min = math.log(self.min_speed)
        log_max = math.log(self.max_speed)
        log_value = log_min + (log_max - log_min) * (1 - position_ratio)
        self.value = math.exp(log_value)
        return self.value

    def render(self):
        # 绘制滑块轨道
        pygame.draw.rect(screen, GRAY, self.rect)
        # 绘制滑块按钮
        pygame.draw.rect(screen, BLUE, self.knob)
        # 绘制速度文本（显示毫秒）
        font = pygame.font.Font(None, 24)
        speed_text = font.render(f'速度: {self.value*1000:.0f}毫秒', True, WHITE)
        screen.blit(speed_text, (self.rect.x, self.rect.y - 20))

# 方向常量 - 现在使用角度来表示方向
class Direction:
    def __init__(self, angle):
        self.angle = angle
        self.update_vector()
    
    def update_vector(self):
        # 将角度转换为弧度
        rad = math.radians(self.angle)
        # 计算方向向量
        self.dx = round(math.cos(rad), 2)
        self.dy = round(math.sin(rad), 2)
    
    def get_vector(self):
        return (self.dx, self.dy)

# 蛇类
class Snake:
    def __init__(self):
        self.length = 1
        self.positions = [(WINDOW_WIDTH//2, WINDOW_HEIGHT//2)]
        self.direction = Direction(0)  # 初始方向向右
        self.color = GREEN
        self.score = 0
        self.speed = 5  # 移动速度
        self.is_dragonfly = False  # 新增：是否变身蜻蜓
        self.dragonfly_timer = 0   # 新增：蜻蜓状态计时器

    def get_head_position(self):
        return self.positions[0]

    def update(self):
        # 更新蜻蜓状态
        if self.is_dragonfly:
            self.dragonfly_timer -= 1
            if self.dragonfly_timer <= 0:
                self.is_dragonfly = False

        cur = self.get_head_position()
        dx, dy = self.direction.get_vector()
        # 根据速度值调整移动距离
        move_distance = BLOCK_SIZE * (0.2 / self.speed)  # 速度越大，移动距离越小
        new_x = (cur[0] + (dx * move_distance)) % WINDOW_WIDTH
        new_y = (cur[1] + (dy * move_distance)) % WINDOW_HEIGHT
        new = (new_x, new_y)

        if not self.is_dragonfly:  # 非蜻蜓状态才检查碰撞
            for pos in self.positions[3:]:
                if abs(new[0] - pos[0]) < BLOCK_SIZE/2 and abs(new[1] - pos[1]) < BLOCK_SIZE/2:
                    return False

        self.positions.insert(0, new)
        if len(self.positions) > self.length:
            self.positions.pop()
        return True

    def turn(self, angle_change):
        new_angle = (self.direction.angle + angle_change) % 360
        self.direction = Direction(new_angle)

    def reset(self):
        self.length = 1
        self.positions = [(WINDOW_WIDTH//2, WINDOW_HEIGHT//2)]
        self.direction = Direction(0)
        self.score = 0

    def render(self):
        # 绘制身体
        for i, p in enumerate(self.positions):
            if i == 0 and self.is_dragonfly:  # 如果是头部且处于蜻蜓状态
                screen.blit(DRAGONFLY_IMG, (p[0]-BLOCK_SIZE/2, p[1]-BLOCK_SIZE/2))
            else:
                pygame.draw.rect(screen, self.color, (p[0]-BLOCK_SIZE/2, p[1]-BLOCK_SIZE/2, BLOCK_SIZE, BLOCK_SIZE))

    def transform_to_dragonfly(self):
        """变身为蜻蜓状态"""
        self.is_dragonfly = True
        self.dragonfly_timer = 300  # 10秒（假设30帧/秒）

# 食物类
class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = RED
        self.randomize_position()

    def randomize_position(self):
        self.position = (random.randint(0, (WINDOW_WIDTH-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE,
                        random.randint(0, (WINDOW_HEIGHT-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE)

    def render(self):
        pygame.draw.rect(screen, self.color, (self.position[0], self.position[1], BLOCK_SIZE, BLOCK_SIZE))

# 向日葵类
class Sunflower:
    def __init__(self):
        self.position = (0, 0)
        self.active = False
        self.randomize_position()

    def randomize_position(self):
        self.position = (random.randint(0, (WINDOW_WIDTH-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE,
                        random.randint(0, (WINDOW_HEIGHT-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE)
        self.active = True

    def render(self):
        if self.active:
            screen.blit(SUNFLOWER_IMG, self.position)

def main():
    clock = pygame.time.Clock()
    snake = Snake()
    food = Food()
    slider = SpeedSlider(SLIDER_X, SLIDER_Y, SLIDER_WIDTH, SLIDER_HEIGHT)
    sunflowers = [Sunflower() for _ in range(3)]  # 创建3个向日葵
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    snake.turn(15)  # 向左转15度
                elif event.key == pygame.K_RIGHT:
                    snake.turn(-15)  # 向右转15度
            # 处理滑块事件
            slider.handle_event(event)

        # 更新蛇的速度
        snake.speed = slider.value

        # 更新蛇的位置
        if not snake.update():
            snake.reset()
            food.randomize_position()
            for sunflower in sunflowers:
                sunflower.randomize_position()

        # 检查是否吃到食物
        head_pos = snake.get_head_position()
        if (abs(head_pos[0] - food.position[0]) < BLOCK_SIZE and 
            abs(head_pos[1] - food.position[1]) < BLOCK_SIZE):
            snake.length += 1
            snake.score += 1
            food.randomize_position()

        # 检查是否吃到向日葵
        for sunflower in sunflowers:
            if (sunflower.active and 
                abs(head_pos[0] - sunflower.position[0]) < BLOCK_SIZE and 
                abs(head_pos[1] - sunflower.position[1]) < BLOCK_SIZE):
                sunflower.active = False
                snake.transform_to_dragonfly()
                snake.score += 5  # 额外奖励5分
                # 随机在新位置生成一个向日葵
                if random.random() < 0.3:  # 30%的概率生成新的向日葵
                    inactive_sunflowers = [s for s in sunflowers if not s.active]
                    if inactive_sunflowers:
                        random.choice(inactive_sunflowers).randomize_position()

        # 绘制
        screen.fill(BLACK)
        snake.render()
        food.render()
        for sunflower in sunflowers:
            sunflower.render()
        slider.render()
        
        # 显示分数和状态
        font = pygame.font.Font(None, 36)
        score_text = font.render(f'得分: {snake.score}', True, WHITE)
        screen.blit(score_text, (10, 10))
        
        if snake.is_dragonfly:
            dragonfly_text = font.render(f'蜻蜓状态: {snake.dragonfly_timer//30}秒', True, BLUE)
            screen.blit(dragonfly_text, (10, 50))
        
        pygame.display.update()
        # 使用速度值来控制帧率
        clock.tick(1 / snake.speed)  # 将速度值直接用作更新间隔

if __name__ == '__main__':
    main() 