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
#ifndef TCOD_GUI_TEXTBOX_HPP
#define TCOD_GUI_TEXTBOX_HPP
#ifndef TCOD_NO_UNICODE
#include "widget.hpp"
class TCODLIB_GUI_API TextBox : public Widget {
 public:
  TextBox(int x, int y, int w, int max_width, const char* label, const char* value, const char* tip = NULL);
  virtual ~TextBox();
  void render();
  void update(const TCOD_key_t k);
  void setText(const char* txt);
  const char* getValue() { return txt; }
  void setCallback(void (*cbk)(Widget* wid, char* val, void* data), void* data_) {
    text_callback = cbk;
    this->data = data_;
  }
  static void setBlinkingDelay(float delay) { blinkingDelay = delay; }

 protected:
  static float blinkingDelay;
  char* label;
  char* txt;
  float blink;
  int pos, offset;
  int box_x, box_width, max_width;
  bool insert;
  void (*text_callback)(Widget* wid, char* val, void* data);
  void* data;

  void onButtonClick();
};
#endif  // TCOD_NO_UNICODE
#endif /* TCOD_GUI_TEXTBOX_HPP */
