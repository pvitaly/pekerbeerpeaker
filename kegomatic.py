#!/usr/bin/python
import os
import time
import math
import logging
import pygame, sys
from pygame.locals import *
import RPi.GPIO as GPIO
from flowmeter import *
from adabot import *
import csv
from datetime import datetime

#boardRevision = GPIO.RPI_REVISION
GPIO.setmode(GPIO.BCM) # use real GPIO numbering
GPIO.setup(18,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(23,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(12,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(21,GPIO.IN, pull_up_down=GPIO.PUD_UP)

# set up pygame
pygame.init()

# set up the window
VIEW_WIDTH = 1248
VIEW_HEIGHT = 688
pygame.display.set_caption('KEGBOT')
lastTweet = 0
view_mode = 'normal'

# hide the mouse
pygame.mouse.set_visible(False)

# set up the flow meters
fm = FlowMeter('metric', 'Not-So-Skinny Dip', 3.6, 1, 18)
fm2 = FlowMeter('metric', 'Irish Hills Red', 4, 2, 23)
fm3 = FlowMeter('metric', 'Water', 3.82, 3, 12)
fm4 = FlowMeter('metric', 'One & Only Hearted', 3.6, 4, 21)
tweet = ''

# set up the colors
BLACK = (0,0,0)
WHITE = (255,255,255)

# set up the window surface
windowSurface = pygame.display.set_mode((VIEW_WIDTH,VIEW_HEIGHT), FULLSCREEN, 32)
windowInfo = pygame.display.Info()
FONTSIZE = 48
LINEHEIGHT = 28
basicFont = pygame.font.SysFont(None, FONTSIZE)

# set up the backgrounds
bg = pygame.image.load('beer-bg.png')
tweet_bg = pygame.image.load('tweet-bg.png')

# set up the adabots
back_bot = adabot(361, 151, 361, 725)
middle_bot = adabot(310, 339, 310, 825)
front_bot = adabot(220, 527, 220, 888)

# draw some text into an area of a surface
# automatically wraps words
# returns any text that didn't get blitted
def drawText(surface, text, color, rect, font, aa=False, bkg=None):
    rect = Rect(rect)
    y = rect.top
    lineSpacing = -2

    # get the height of the font
    fontHeight = font.size("Tg")[1]

    while text:
        i = 1

        # determine if the row of text will be outside our area
        if y + fontHeight > rect.bottom:
            break

        # determine maximum width of line
        while font.size(text[:i])[0] < rect.width and i < len(text):
            i += 1

        # if we've wrapped the text, then adjust the wrap to the last word
        if i < len(text):
            i = text.rfind(" ", 0, i) + 1

        # render the line and blit it to the surface
        if bkg:
            image = font.render(text[:i], 1, color, bkg)
            image.set_colorkey(bkg)
        else:
            image = font.render(text[:i], aa, color)

        surface.blit(image, (rect.left, y))
        y += fontHeight + lineSpacing

        # remove the text we just blitted
        text = text[i:]

    return text

def renderThings(tweet, windowSurface, basicFont):
  # Clear the screen
  windowSurface.blit(bg,(0,0))

  # draw the adabots
  back_bot.update()
  windowSurface.blit(back_bot.image,(back_bot.x, back_bot.y))
  middle_bot.update()
  windowSurface.blit(middle_bot.image,(middle_bot.x, middle_bot.y))
  front_bot.update()
  windowSurface.blit(front_bot.image,(front_bot.x, front_bot.y))

  # Draw Ammt Poured
  text = basicFont.render("CURRENT", True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (40,20))
  if fm.enabled:
    text = basicFont.render(fm.getFormattedThisPour(), True, WHITE, BLACK)
    textRect = text.get_rect()
    windowSurface.blit(text, (40,30+LINEHEIGHT))
  if fm2.enabled:
    text = basicFont.render(fm2.getFormattedThisPour(), True, WHITE, BLACK)
    textRect = text.get_rect()
    windowSurface.blit(text, (40, 30+(2*(LINEHEIGHT+5))))
  if fm3.enabled:
	text = basicFont.render(fm3.getFormattedThisPour(), True, WHITE, BLACK)
	textRect = text.get_rect()
	windowSurface.blit(text, (40, 30+(3*(LINEHEIGHT+7))))
  if fm4.enabled:
	text = basicFont.render(fm4.getFormattedThisPour(), True, WHITE, BLACK)
	textRect = text.get_rect()
	windowSurface.blit(text, (40, 30+(4*(LINEHEIGHT+9))))

  # Draw Ammt Poured Total
  text = basicFont.render("TOTAL", True, WHITE, BLACK)
  textRect = text.get_rect()
  windowSurface.blit(text, (windowInfo.current_w - textRect.width - 40, 20))
  if fm.enabled:
    text = basicFont.render(fm.getFormattedTotalPour(), True, WHITE, BLACK)
    textRect = text.get_rect()
    windowSurface.blit(text, (windowInfo.current_w - textRect.width - 40, 30 + LINEHEIGHT))
  if fm2.enabled:
    text = basicFont.render(fm2.getFormattedTotalPour(), True, WHITE, BLACK)
    textRect = text.get_rect()
    windowSurface.blit(text, (windowInfo.current_w - textRect.width - 40, 30 + (2 * (LINEHEIGHT+5))))
  if fm3.enabled:
	text = basicFont.render(fm3.getFormattedTotalPour(), True, WHITE, BLACK)
	textRect = text.get_rect()
	windowSurface.blit(text, (windowInfo.current_w - textRect.width - 40, 30 + (3 * (LINEHEIGHT+7))))
  if fm4.enabled:
	text = basicFont.render(fm4.getFormattedTotalPour(), True, WHITE, BLACK)
  	textRect = text.get_rect()
	windowSurface.blit(text, (windowInfo.current_w - textRect.width - 40, 30 + (4 * (LINEHEIGHT+9))))

  if view_mode == 'tweet':
	windowSurface.blit(tweet_bg,(0,0))
	textRect = Rect(545,265,500,225)
	drawText(windowSurface, tweet, BLACK, textRect, basicFont, True, None)

  # Display everything
  pygame.display.flip()

def tweetPour(theTweet):
  try:
    t.statuses.update(status=theTweet)
  except:
    logging.warning('Error tweeting: ' + theTweet + "\n")

GPIO.add_event_detect(18, GPIO.RISING, callback=fm.channelRead, bouncetime=20) # Not So Skinny Dip
GPIO.add_event_detect(23, GPIO.RISING, callback=fm2.channelRead, bouncetime=20) # Irish Hills Red
GPIO.add_event_detect(12, GPIO.RISING, callback=fm3.channelRead, bouncetime=20) # Water
GPIO.add_event_detect(21, GPIO.RISING, callback=fm4.channelRead, bouncetime=20) # One and Only Hearted


def writeToCsv(flowmeter):
  with open('taps.csv', 'ab') as csvfile:
	tapWriter = csv.writer(csvfile, delimiter=',', quotechar= '|', quoting=csv.QUOTE_MINIMAL)
	tapWriter.writerow([str(flowmeter.tap), str(flowmeter.dataPin), str(flowmeter.beverage), str(datetime.now()), str(flowmeter.thisPour), str(flowmeter.totalPour)])

def writeTotalsToCsv(flowmeter):
	newcsv = []
    with open('total-taps.csv', 'rb') as csvfile:
      tapsReader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in tapsReader:
			if row[0] == str(flowmeter.tap):
              row[4] = str(flowmeter.totalPour)

			newcsv.append(row)

	with open('total-taps.csv', 'wb') as csvfile:
		tapWriter = csv.writer(csvfile, delimiter=',', quotechar = '|', quoting=csv.QUOTE_MINIMAL)
        for line in newcsv:
          tapWriter.writerow(line)
def printPour(flowmeter, currentTime):
  if (flowmeter.thisPour > 0.0443603 and (currentTime - flowmeter.lastClick) > 5000): # after 5 seconds of inactivity write info to file
	tweet = "You just poured " + fm.getFormattedThisPour() + " of " + fm.getBeverage() + " at Peker Brewing Co."
	lastTweet = int(time.time() * FlowMeter.MS_IN_A_SECOND)
	writeToCsv(flowmeter)
	writeTotalsToCsv(flowmeter)
	flowmeter.thisPour = 0.0
	return tweet

# main loop
while True:
  # Handle keyboard events
  for event in pygame.event.get():
    if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
      GPIO.cleanup()
      pygame.quit()
      sys.exit()
    elif event.type == KEYUP and event.key == K_1:
      fm.enabled = not(fm.enabled)
    elif event.type == KEYUP and event.key == K_2:
      fm2.enabled = not(fm2.enabled)
    elif event.type == KEYUP and event.key == K_9:
      fm.clear()
    elif event.type == KEYUP and event.key == K_0:
      fm2.clear()

  currentTime = int(time.time() * FlowMeter.MS_IN_A_SECOND)

  if currentTime - lastTweet < 5000: # Pause for 5 seconds after tweeting to show the tweet
    view_mode = 'tweet'
  else:
    view_mode = 'normal'

  printPour(fm, currentTime)
  printPour(fm2, currentTime)
  printPour(fm3, currentTime)
  printPour(fm4, currentTime)

  renderThings(tweet, windowSurface, basicFont)
