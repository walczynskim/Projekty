'''
--------------------------------------------------------------------------------
   Spacecraft, wideogra stworzona za pomocą Pythona i PyQt 
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
'''



from math import pi

SPACECRAFT_LENGTH = 20

SPACECRAFT_MASS = 1.
BULLET_MASS = 0.01

INITIAL_SPEED = 0*200j
INITIAL_POSITION = 100+500j

THRUST_FORCE = 4000.
LATERAL_THRUST_FORCE = 2000.

GRAVITY_ACCELERATION = 0*800j

TIMER_ELAPSE = 25 #w ms
BULLET_SPEED = 800.
BOUNCING_BULLET_SPEED = 400.
BULLET_AGE_MAX_IN_SEC = 20
BULLET_AGE_MAX = BULLET_AGE_MAX_IN_SEC * 1000/TIMER_ELAPSE
REARM1_PERIOD =  3  #w TIMER_ELAPSE
REARM2_PERIOD =  8  #w TIMER_ELAPSE

import sys
import time
from math import pi, cos, sin
from random import uniform

from PyQt4.QtCore import *
from PyQt4.QtGui import *


class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        self.setupWindow()
        self.installEventFilter(self)
        self.setWindowState(self.windowState() | Qt.WindowFullScreen)
        self.setCursor(Qt.BlankCursor)
        self.tgtImageLabel.setFocus(Qt.OtherFocusReason)
      
    def setupWindow(self):
        self.resize(800,600)
        self.tgtImageLabel = SpaceSceneWidget(self)
        self.setCentralWidget(self.tgtImageLabel)


class SpaceSceneWidget(QWidget): 

    def __init__(self,parent):
        QWidget.__init__(self,parent)
        self.r = 10
        self.inc = 1
        self.pressedKeys = set()
        screenGeometry = QApplication.desktop().screenGeometry()
        self.spaceScene = SpaceScene(screenGeometry.width(),screenGeometry.height())
        self.spaceScene.pressedKeys = self.pressedKeys
        self.spaceScene.setupLevel()
        self.defaultBrush = QBrush(QColor(200,200,200))
        self.timer = QTimer()
        QObject.connect(self.timer,SIGNAL('timeout()'),self.timerEvent)
        self.timer.start(TIMER_ELAPSE)

    def keyPressEvent(self,keyEvent):
        if keyEvent.isAutoRepeat():
            keyEvent.ignore()
            return
        keyEvent.accept()
        key = keyEvent.key()
        if key == Qt.Key_F11:
            parent = self.parent()
            parent.setWindowState(parent.windowState() | Qt.WindowFullScreen)
            self.setCursor(Qt.BlankCursor)
        elif key == Qt.Key_Escape:
            parent = self.parent()            
            parent.setWindowState(parent.windowState() & ~Qt.WindowFullScreen)
            self.setCursor(Qt.ArrowCursor)
        elif key == Qt.Key_T:
            self.spaceScene.resetLevel()
            self.spaceScene.setupLevel()
        self.pressedKeys.add(key)

    def keyReleaseEvent(self,keyEvent):
        if keyEvent.isAutoRepeat():
            keyEvent.ignore()
            return   
        self.pressedKeys.remove(keyEvent.key())
        keyEvent.accept()

    def timerEvent(self):
        self.spaceScene.update()
        self.update()

    def paintEvent(self,paintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.geometry(),Qt.black)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.defaultBrush)
        self.spaceScene.draw(painter)


class SpaceScene(object):

    def __init__(self,width,height):
        self.width = width
        self.height = height
        self.resetLevel()
        self.pressedKeys = None

    def resetLevel(self):
        self.bodies = []
        self.bullets = []
        self.walls = []
        self.mines = []
        self.destroyableGroups = []

    def setupLevel(self):
        spacecraft1 = Spacecraft(50+self.height/2*1j,0.,0.)
        spacecraft2 = Spacecraft(self.width-50+self.height/2*1j,0.,pi)
        self.spacecrafts = (spacecraft1,spacecraft2)
        spacecraft1.mapKeys(Qt.Key_X,Qt.Key_C,Qt.Key_A,Qt.Key_Q,Qt.Key_Control,Qt.Key_W)
        spacecraft1.setColor(QColor(128,255,128))
        self.addBody(spacecraft1)
        self.addBody(spacecraft2)
        self.addWall(Wall(0,0,self.width,10))
        self.addWall(Wall(0,0,10,self.height))
        self.addWall(Wall(self.width-10,0,10,self.height))
        self.addWall(Wall(0,self.height-10,self.width,10))
        self.addWall(Wall(100,self.height/2-40,20,80))
        self.addWall(Wall(self.width-100-20,self.height/2-40,20,80))
        self.addWall(Wall(self.width/2-30,0,60,100))
        self.addWall(Wall(self.width/2-30,self.height-100,60,100))
      
        destroyables = []        
        for x in range(4):
            for y in range(41):
                destroyables.append(Destroyable(self.width/2-40+20*x,self.height/2-41*10+20*y,20,20))

        for x in range(2):
            for y in range(4):
                self.addMine(Mine(self.width/2-100-120*x,self.height/2-3*120/2+120*y,15,self)) 
                self.addMine(Mine(self.width/2+100+120*x,self.height/2-3*120/2+120*y,15,self)) 

        self.addDestroyableGroup(GroupOfItems(destroyables))        
        destroyables = []        
        self.update()
        SoundManager.startSound.play()
      
    def addBody(self,body):
        self.bodies.append(body)
        body.spaceScene = self

    def addWall(self,wall):
        self.walls.append(wall)

    def addMine(self,mine):
        self.mines.append(mine)

    def addDestroyableGroup(self,destroyableGroup):
        self.destroyableGroups.append(destroyableGroup)
  
    def addBullet(self,pos,speed):
        bullet = Bullet(pos,speed)
        self.addBody(bullet)
        self.bullets.append(bullet)
        return bullet

    def add3Bullets(self,pos,speed,dir_):
        g = dir_*1j / abs(dir_)
        gs = 4 * g
        gp = 6 * g
        pos -= gp
        speed -= gs
        for i in range(3):
            bullet = Bullet(pos,speed)
            self.addBody(bullet)
            self.bullets.append(bullet)
            pos += gp
            speed += gs

    def removeBullets(self):
        for bullet in self.bullets[:]:
            self.bodies.remove(bullet)
            self.bullets.remove(bullet)
      
    def update(self):
        for spacecraft in self.spacecrafts:
            spacecraft.processPressedKeys()
        for body in self.bodies:
            body.update()
        for destroyableGroup in self.destroyableGroups:
            destroyableGroup.update()

        minesToDelete = []
        for mine in self.mines:
            mine.update()
            if mine.lifetime == 0:
                minesToDelete.append(mine)
        for mine in minesToDelete:
            self.mines.remove(mine)

        bulletsToDelete = []
        for bullet in self.bullets:
            if bullet.lifetime == 0:
                bulletsToDelete.append(bullet)
            elif not bullet.exploding:
                for spacecraft in self.spacecrafts:
                    if not spacecraft.exploding and spacecraft.collidesPoint(bullet.position):
                        SoundManager.explosionSound.play()
                        bullet.explode()
                        spacecraft.explode()
                if not bullet.exploding:                      
                    for wall in self.walls:
                        if wall.collidesPoint(bullet.position):
                            if bullet.bouncing:
                                dirWall = wall.nearestArc2(bullet.prevPosition,bullet.position)
                                bullet.bounce(dirWall)
                            else:
                                bullet.explode()
                            break
                if not bullet.exploding:
                    for mine in self.mines:
                        if mine.collidesPoint(bullet.position):
                            bullet.explode()
                            mine.explode()
                            break                  
                if not bullet.exploding:
                    for destroyableGroup in self.destroyableGroups:
                        collidedDestroyable = destroyableGroup.collidedItemWithPoint(bullet.position)
                        if collidedDestroyable is not None:
                            bullet.explode()
                            collidedDestroyable.explode()
                            break
        for bullet in bulletsToDelete:                
            self.bodies.remove(bullet)
            self.bullets.remove(bullet)
        for spacecraft in self.spacecrafts:
            if not spacecraft.exploding:
                for wall in self.walls:
                    collisionPoint = spacecraft.collisionPoint(wall.polygon)
                    if collisionPoint is not None:
                        nearestArc = wall.nearestArc(collisionPoint)
                        spacecraft.bounceOnFixedPoint(collisionPoint,nearestArc)
                        break
        for spacecraft in self.spacecrafts:
            if not spacecraft.exploding:
                for destroyableGroup in self.destroyableGroups:
                    (collidedDestroyable,collisionPoint) = destroyableGroup.collidedItemWithPolygon(spacecraft.polygon)
                    if collidedDestroyable is not None:
                        nearestArc = collidedDestroyable.nearestArc(collisionPoint)
                        spacecraft.bounceOnFixedPoint(collisionPoint,nearestArc)
                        collidedDestroyable.explode()
            if not spacecraft.exploding:
                for mine in self.mines:
                    if mine.collidesPolygon(spacecraft.polygon):
                        mine.explode()

        if not self.spacecrafts[0].exploding and not self.spacecrafts[1].exploding:
            collisionPoint0 = self.spacecrafts[0].collisionPoint(self.spacecrafts[1].polygon)
            if collisionPoint0 is not None:
                collisionPoint1 = self.spacecrafts[1].collisionPoint(self.spacecrafts[0].polygon)
                arc = 1j * (self.spacecrafts[1].position-self.spacecrafts[0].position)
                arc /= abs(arc)
                self.spacecrafts[0].bounceOnFixedPoint(collisionPoint0,arc)
                self.spacecrafts[1].bounceOnFixedPoint(collisionPoint1,arc)
                self.spacecrafts[0].explode()
                self.spacecrafts[1].explode()

             
    def draw(self,painter):
        for wall in self.walls:
            wall.draw(painter)
        for mine in self.mines:
            mine.draw(painter)
        for destroyableGroup in self.destroyableGroups:
            destroyableGroup.draw(painter)
        for body in self.bodies:
            body.draw(painter)

class Mine(object): 

    def __init__(self,x,y,r,spaceScene):
        self.c = x + y*1j
        self.r = r
        self.spaceScene = spaceScene
        self.rect = QRect(x-r,y-r,2*r,2*r)
        self.lifetime = -1
        self.exploding = False
        self.mineBrush = QBrush(QColor(255,0,255))
      
    def draw(self,painter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.mineBrush)
        painter.drawEllipse(self.rect)

    def collidesPoint(self,p):
        return abs(p-self.c) <= self.r

    def collidesPolygon(self,polygon):
        # przybliżenie!
        for i in range(polygon.size()):
            point = polygon[i]
            if self.collidesPoint(complex(point.x(),point.y())):
                return True
        return False      

    def update(self):
        if self.exploding:
            self.lifetime -= 1
            if self.lifetime == 0:
                for i in range(10):
                    a = uniform(0.,2.*pi)
                    v = uniform(0.,80.)+uniform(0.,80.)+uniform(0.,80.)+uniform(0.,80.)
                    bullet = self.spaceScene.addBullet(self.c,v*complex(cos(a),sin(a)))
                    bullet.setColor(QColor(255,255,0))

    def explode(self):
        self.lifetime = 1
        self.exploding = True


class Wall(object):

    def __init__(self,x,y,w,h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = QRect(x,y,w,h)
        self.polygon = QPolygon(self.rect,True)
        self.wallBrush = QBrush(QColor(0,255,255))
      
    def getBoundingBox(self):
        return (self.x,self.x+self.w,self.y,self.y+self.h)
      
    def update(self):
        pass  

    def draw(self,painter):
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.wallBrush)
        painter.drawRect(self.rect)

    def collidesPoint(self,p):
        return self.rect.contains(p.real,p.imag)
  
    def nearestArc(self,p):
        distMin = 9e99
        for i in range(1,self.polygon.size()):
            point1 = self.polygon[i-1]
            point2 = self.polygon[i]
            p1 = complex(point1.x(),point1.y())
            p2 = complex(point2.x(),point2.y())
            dist = (abs(p-p1)+abs(p-p2)) / abs(p2-p1)
            if dist < distMin:
                distMin = dist
                tangentialDir = p2 - p1
        return tangentialDir / abs(tangentialDir)       
  
    def nearestArc2(self,prevP,p):
        for i in range(1,self.polygon.size()):
            point1 = self.polygon[i-1]
            point2 = self.polygon[i]
            p1 = complex(point1.x(),point1.y())
            p2 = complex(point2.x(),point2.y())
            d = p1.real*p2.imag - p1.imag*p2.real
            s1 = (p2.imag-p1.imag)*p.real - (p2.real-p1.real)*p.imag - d
            s2 = (p2.imag-p1.imag)*prevP.real - (p2.real-p1.real)*prevP.imag - d
            if (s1>0.) != (s2>0.):
                tangentialDir = p2 - p1
                break
        return tangentialDir / abs(tangentialDir)       


class GroupOfItems(object):

    def __init__(self,items):
        (xmin,xmax,ymin,ymax) = (maxint,-1,maxint,-1)
        self.items = items
        for item in items:
            (xmin0,xmax0,ymin0,ymax0) = item.getBoundingBox()
            xmin = min(xmin0,xmin)
            xmax = max(xmax0,xmax)
            ymin = min(ymin0,ymin)
            ymax = max(ymax0,ymax)
        self.rect = QRect(xmin,ymin,xmax-xmin,ymax-ymin)
        self.polygon = QPolygon(self.rect,True)

    def update(self):
        itemsToDelete = []
        for item in self.items:
            item.update()
            if item.lifetime == 0:
                itemsToDelete.append(item)
        for item in itemsToDelete:
            self.items.remove(item)

    def draw(self,painter):
        for item in self.items:
            item.draw(painter)
      
    def collidedItemWithPoint(self,point):
        if self.rect.contains(point.real,point.imag):
            for item in self.items:
                if item.collidesPoint(point):
                    return item
        return None
                                   
    def collidedItemWithPolygon(self,polygon):
        if not self.polygon.intersected(polygon).isEmpty():
            for item in self.items:
                if not item.exploding:
                    collisionPolygon = item.polygon.intersected(polygon)
                    if not collisionPolygon.isEmpty():
                        mc = 0+0j
                        #Ostatni punkt jest zarazem pierwszym, więc nie uwzględnia się go
                        nbPoints = collisionPolygon.size() - 1
                        for i in range(nbPoints):
                            point = collisionPolygon[i]
                            mc += complex(point.x(),point.y())
                        return (item, mc/nbPoints)
        return (None, None)


class Destroyable(object):

    def __init__(self,x,y,w,h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = QRect(x,y,w,h)
        self.polygon = QPolygon(self.rect,True)
        self.wallBrush = QBrush(QColor(127,0,127))
        self.wallPen = QPen(QColor(0,127,0))
        self.lifetime = -1
        self.exploding = False

    def getBoundingBox(self):
        return (self.x,self.x+self.w,self.y,self.y+self.h)
      
    def update(self):
        if self.exploding:
            self.lifetime -= 1

    def draw(self,painter):
        if self.exploding:
            pen = QPen(QColor(0,100,0,12*self.lifetime))
            brush = QBrush(QColor(127,0,127,12*self.lifetime),Qt.Dense4Pattern)
        else:    
            pen = self.wallPen
            brush = self.wallBrush
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRect(self.rect)

    def collidesPoint(self,p):
        if self.exploding:
            return False
        return self.rect.contains(p.real,p.imag)

    def explode(self):
        self.exploding = True
        self.lifetime = 20     

    def nearestArc(self,p):
        distMin = 9e99
        for i in range(1,self.polygon.size()):
            point1 = self.polygon[i-1]
            point2 = self.polygon[i]
            p1 = complex(point1.x(),point1.y())
            p2 = complex(point2.x(),point2.y())
            dist = (abs(p-p1)+abs(p-p2)) / abs(p2-p1)
            if dist < distMin:
                distMin = dist
                tangentialDir = p2 - p1
        return tangentialDir / abs(tangentialDir)       


class Bullet(object): 

    def __init__(self,pos,speed):
        self.__init__(self,BULLET_MASS,1,pos,speed) 
        self.spaceScene = None
        self.setCentralAcceleration(GRAVITY_ACCELERATION)
        self.lifetime = BULLET_AGE_MAX
        self.exploding = False
        self.setBouncing(False)

    def setBouncing(self,bouncing):
        self.bouncing = bouncing
        if bouncing:
            color = QColor(127,127,127)
        else:
            color = QColor(240,240,240)
        self.setColor(color)
       
    def setColor(self,color):
        self.bulletPen = QPen(color)
      
    def update(self):
        Body.update(self)
        self.lifetime -= 1

    def draw(self,painter):
        p = self.position
        if self.exploding:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255,240,200,12*self.lifetime)))
            r = (21-self.lifetime)/2
            if r > 0:
                painter.drawEllipse(p.real-r,p.imag-r,2*r,2*r)
        else:    
            painter.setPen(self.bulletPen)
            painter.drawPoint(p.real,p.imag)
            painter.drawPoint(p.real+1,p.imag)
            painter.drawPoint(p.real,p.imag+1)
            painter.drawPoint(p.real+1,p.imag+1)

    def explode(self):
        self.exploding = True
        self.lifetime = 20     
        self.setCentralAcceleration(0)
        self.setV(0)


class Spacecraft(object): 

    def __init__(self,position,speed,angle):
        self.__init__(self, SPACECRAFT_MASS, 25., position,speed,angle) 
        self.dragCoefficientV = 1.
        self.dragCoefficientW = 150.
        self.initialPosition = self.position
        self.initialV = self.v
        self.initialA = self.a
        self.spaceScene = None
        self.setCentralAcceleration(GRAVITY_ACCELERATION)
        self.setSize(SPACECRAFT_LENGTH)
      
        self.flamePen = QPen(QColor(250,180,0))
        self.flamePen.setWidth(2)
        self.fire1Pen = QPen(QColor(240,240,0))
        self.fire1Pen.setWidth(5)
        self.fire2Pen = QPen(QColor(127,255,127))
        self.fire2Pen.setWidth(9)
        self.polygon = QPolygon(3)
        self.setColor(QColor(170,170,255))
        self.explosionBrush = QBrush(QColor(240,0,0))
        self.leftKey = Qt.Key_Left
        self.rightKey = Qt.Key_Right
        self.fwdThrustKey = Qt.Key_Up
        self.revThrustKey = Qt.Key_Down
        self.fire1Key = Qt.Key_M
        self.fire2Key = Qt.Key_L
        self.g = 0
        self.restart()

    def setSize(self,size):
        self.headL =  size * 2. / 3.
        self.tailL = size  * 1. / 3.
        self.halfWidth = size  * 1. / 3.
        self.flameL = size * 1. / 3.

    def mapKeys(self,leftKey,rightKey,fwdThrustKey,revThrustKey,fire1Key,fire2Key):
        (self.leftKey,self.rightKey,self.fwdThrustKey,self.revThrustKey,self.fire1Key,self.fire2Key) \
        = (leftKey,rightKey,fwdThrustKey,revThrustKey,fire1Key,fire2Key)

    def setColor(self,color):
        self.spacecraftBrush = QBrush(color)
        self.spacecraftPen = QPen(color.lighter(150))
        self.spacecraftPen.setWidth(2)

    def restart(self): 
        SoundManager.controlSound.play()
        self.lifetime = -1
        self.exploding = False
        self.canFire1 = True
        self.canFire2 = True
        self.rearm1Counter = 0
        self.rearm2Counter = 0
        self.setP(self.initialPosition)
        self.setV(self.initialV)
        self.setA(self.initialA)
        self.setW(0.)

    def recalcPolygon(self):
        p = self.position
        d = self.dir      
        dp = d * 1j
        p1 = p - self.tailL*d + self.halfWidth*dp
        p2 = p + self.headL*d
        p3 = p - self.tailL*d - self.halfWidth*dp
        self.polygon.setPoints(p1.real,p1.imag,p2.real,p2.imag,p3.real,p3.imag) #,p1.real,p1.imag)

    def update(self):
        Body.update(self)     
        if self.exploding:
            self.lifetime -= 1
            if self.lifetime == 0:
                self.restart()
        if not self.exploding:
            self.recalcPolygon()
            if not self.canFire1:
                if self.rearm1Counter == 0:
                    self.canFire1 = True
                self.rearm1Counter -= 1
            if not self.canFire2:
                if self.rearm2Counter == 0:
                    self.canFire2 = True
                self.rearm2Counter -= 1

    def bounceOnFixedPoint(self,point,wallDir):
        Body.bounceOnFixedPoint(self,point,wallDir)
        self.recalcPolygon()

    def collidesPoint(self,p):
        return self.polygon.containsPoint(QPoint(p.real,p.imag),Qt.OddEvenFill)
  
    def collisionPoint(self,polygon):
        intersectionPolygon = self.polygon.intersected(polygon)
        if not intersectionPolygon.isEmpty():
            mc = 0+0j
            #Ostatnie punkt jest takie samy jak pierwszy, dlatego  jest wykluczony
            for i in range(intersectionPolygon.size()-1):
                point = intersectionPolygon[i]
                mc += complex(point.x(),point.y())
            collisionPoint = mc / (intersectionPolygon.size()-1)
            #Znaleźć najbliższy punkt od spacecraft
            points = (complex(p.x(),p.y()) for p in (self.polygon[i] for i in range(self.polygon.size())))
            distMin = 9e99
            for p in points:
                dist = abs(p-collisionPoint)
                if dist < distMin:                  
                    distMin = dist
                    point = p
            return point    
        return None

    def explode(self):
        self.exploding = True
        self.lifetime = 120
        for i in range(20):
            a = uniform(0.,2.*pi)
            v = uniform(0.,40.)+uniform(0.,40.)+uniform(0.,40.)+uniform(0.,40.)
            bullet = self.spaceScene.addBullet(self.position,self.v+v*complex(cos(a),sin(a)))
            bullet.m = self.m
            bullet.dragCoefficientV = self.dragCoefficientV
      
    def draw(self,painter):
        p = self.position
        d = self.dir
        dp = d * 1j
        painter.setPen(Qt.NoPen)
        if self.exploding:
            if self.lifetime > 60:
                painter.setBrush(QBrush(QColor(180,255,180,4*(self.lifetime-60))))
                r = (121-self.lifetime)/4
                if r > 0:
                    painter.drawEllipse(p.real-r,p.imag-r,2*r,2*r)           
        else:
            p1 = p - (self.tailL+2.)*d
            p2 = p + (self.headL+1.)*d
            painter.setPen(self.spacecraftPen)
            painter.drawLine(QPoint(p1.real,p1.imag),QPoint(p2.real,p2.imag))          
            painter.setBrush(self.spacecraftBrush)
            painter.drawConvexPolygon(self.polygon)
            painter.setPen(self.flamePen)
            if self.fwdThrustKey in self.spaceScene.pressedKeys:
                p1 = p - (self.tailL+5.)*d
                p2 = p1 - self.flameL*d
                painter.drawLine(QPoint(p1.real,p1.imag),QPoint(p2.real,p2.imag))
            if self.revThrustKey in self.spaceScene.pressedKeys:              
                p1 = p + (self.headL+2.)*d
                p2 = p1 + self.flameL*d
                painter.drawLine(QPoint(p1.real,p1.imag),QPoint(p2.real,p2.imag))
            if self.fire1Key in self.spaceScene.pressedKeys or self.fire2Key in self.spaceScene.pressedKeys:
                p1 = p + (self.headL+3.)*d
                p2 = p1 + 2.*d
                pen = None
                if self.fire1Key in self.spaceScene.pressedKeys:
                    if self.rearm1Counter > REARM1_PERIOD*.5:
                        pen = self.fire1Pen
                else:
                    if self.rearm2Counter > REARM2_PERIOD*.75:
                        pen = self.fire2Pen
                if pen is not None:        
                    painter.setPen(pen)
                    painter.drawLine(QPoint(p1.real,p1.imag),QPoint(p2.real,p2.imag))
      
    def processPressedKeys(self):
        if not self.exploding:
            isThrustKey = False
            for key in self.spaceScene.pressedKeys:
                if key == self.leftKey:
                    self.applyForce(-1j*self.dir*LATERAL_THRUST_FORCE,self.position+self.dir)
                if key == self.rightKey:
                    self.applyForce(1j*self.dir*LATERAL_THRUST_FORCE,self.position+self.dir)
                if key == self.fwdThrustKey:
                    isThrustKey = True     
                    self.g = (self.g+1)%2     
                    self.applyCentralForce(self.dir*THRUST_FORCE)
                if key == self.revThrustKey:
                    isThrustKey = True     
                    self.g = (self.g+1)%2
                    self.applyCentralForce(-self.dir*THRUST_FORCE)
                if key == self.fire1Key and self.canFire1 \
                or key == self.fire2Key and self.canFire2:
                        canonPos = self.position+(self.headL+1)*self.dir
                        if key == self.fire2Key:
                            bulletSpeed = BOUNCING_BULLET_SPEED
                            #Siła reakcji na spacecraft
                            self.setV(self.v-bulletSpeed*self.dir/30.)
                            self.canFire2 = False
                            self.rearm2Counter = REARM2_PERIOD
                            self.spaceScene.add3Bullets(canonPos,self.getV(canonPos)+bulletSpeed*self.dir,self.dir)
                        else:
                            bulletSpeed = BULLET_SPEED
                            #Siła reakcji na spacecraft
                            self.setV(self.v-bulletSpeed*self.dir/60.)
                            self.canFire1 = False
                            self.rearm1Counter = REARM1_PERIOD
                            self.spaceScene.addBullet(canonPos,self.getV(canonPos)+bulletSpeed*self.dir)
                if key == Qt.Key_Backspace:
                    self.explode()
            if not isThrustKey:
                self.g = 0
        

app = QApplication(sys.argv)
mainWindow = MainWindow()
mainWindow.show()
sys.exit(app.exec_())


