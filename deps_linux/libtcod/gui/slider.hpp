/* BSD 3-Clause License
 *
 * Copyright © 2008-2022, Jice and the libtcod contributors.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from
 *    this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
 * LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */
#ifndef TCOD_GUI_SLIDER_HPP
#define TCOD_GUI_SLIDER_HPP
#ifndef TCOD_NO_UNICODE
#include "textbox.hpp"
class TCODLIB_GUI_API Slider : public TextBox {
 public:
  Slider(int x, int y, int w, float min, float max, const char* label, const char* tip = NULL);
  virtual ~Slider();
  void render();
  void update(const TCOD_key_t k);
  void setMinMax(float min_, float max_) {
    this->min = min_;
    this->max = max_;
  }
  void setCallback(void (*cbk_)(Widget* wid, float val, void* data), void* data_) {
    this->cbk = cbk_;
    this->data = data_;
  }
  void setFormat(const char* fmt);
  void setValue(float value);
  void setSensitivity(float sensitivity_) { this->sensitivity = sensitivity_; }

 protected:
  float min, max, value, sensitivity;
  bool onArrows;
  bool drag;
  int drag_x;
  int drag_y;
  float dragValue;
  char* fmt;
  void (*cbk)(Widget* wid, float val, void* data);
  void* data;

  void valueToText();
  void textToValue();
  void onButtonPress();
  void onButtonRelease();
};
#endif  // TCOD_NO_UNICODE
#endif /* TCOD_GUI_SLIDER_HPP */
