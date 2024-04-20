#pragma once

class UIEntity;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIEntity> data;
} PyUIEntityObject;

class UIFrame;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIFrame> data;
} PyUIFrameObject;

class UICaption;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UICaption> data;
    PyObject* font;
} PyUICaptionObject;

class UIGrid;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIGrid> data;
} PyUIGridObject;

class UISprite;
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UISprite> data;
} PyUISpriteObject;
