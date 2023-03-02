import mcrfpy
mcrfpy.createTexture("./assets/test_portraits.png", 32, 8, 8)
from random import choice, randint

box_colors = [
	(0, 0, 192),
	(0, 192, 0),
	(192, 0, 0),
	(192, 192, 0),
	(0, 192, 192),
	(192, 0, 192)
	]

text_colors = [
	(0, 0, 255),
	(0, 255, 0),
	(255, 0, 0),
	(255, 255, 0),
	(0, 255, 255),
	(255, 0, 255)
	]

test_x = 500
test_y = 10
for i in range(40):
	ui_name = f"test{i}"
	mcrfpy.createMenu(ui_name, test_x, test_y, 400, 200)
	mcrfpy.createCaption(ui_name, "Hello There", 18, choice(text_colors))
	mcrfpy.createButton(ui_name, 250, 20, 100, 50, choice(box_colors), (0, 0, 0), "asdf", "testaction")
	
	mcrfpy.createSprite(ui_name, 0, randint(0, 3), 650, 60, 5.0)

	test_x -= 50
	test_y += 50
	if (test_x <= 50):
		test_x = 500
	#print(test_x)
