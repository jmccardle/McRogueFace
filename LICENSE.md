# About McRogueFace Engine

This software is distributed on Github and other git repos for review & discussion purposes. This engine was made in preparation and during the 2023 7 Day Roguelike game jam. It's not production ready. I don't want to support this buggy version of the software - do not create derivative works, modify, or redistribute this git repo. Not that you'd actually want to: take a close look at the code and you'll quickly find reasons not to depend on the codebase in its present state.

I expect to release the engine under BSD, MIT, or similar license after overhauling my technical debt incurred during the game jam. see JANKFILE.md for outstanding issues.

# Software Licenses

## Dependencies included in this repo

These dependencies were not modified. They're redistributed in this repo because I do not have time to learn git submodules before 7DRL 2023. Headers and shared objects / dynamic libraries are required to build McRogueFace Engine.

In the source code distribution of the engine, files derived from these dependencies can be found in the `deps_linux` and `deps_windows` subdirectories.

### libtcod

* redistributed under the BSD license.
* Version 1.23.1
* Retrieved from https://github.com/libtcod/libtcod .

BSD 3-Clause License

Copyright © 2008-2022, Jice and the libtcod contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

### SFML 

* redistributed under SFML's terms
* Version 2.5.1
* Retrieved from https://www.sfml-dev.org/download/sfml/2.5.1/ .

SFML - Copyright (C) 2007-2018 Laurent Gomila - laurent@sfml-dev.org

This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.

Permission is granted to anyone to use this software for any purpose, including commercial applications, and to alter it and redistribute it freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software.  If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.

#### External libraries used by SFML

  * _OpenAL-Soft_ is under the LGPL license
  * _stb_image_ and _stb_image_write_ are public domain
  * _freetype_ is under the FreeType license or the GPL license
  * _libogg_ is under the BSD license
  * _libvorbis_ is under the BSD license
  * _libflac_ is under the BSD license
 
## Python

* Python environment redistributed under the Python Software Foundation license.
* Python examples were modified to embed Python in the engine. These examples are available under the Zero-Clause BSD license.
* Version 3.11.1
* Retrieved from https://www.python.org/downloads/release/python-3111/ .

Python software and documentation are licensed under the
Python Software Foundation License Version 2.

    Release         Derived     Year        Owner       GPL-
                    from                                compatible? (1)
    2.2 and above   2.1.1       2001-now    PSF         yes

Starting with Python 3.8.6, examples, recipes, and other code in
the documentation are dual licensed under the PSF License Version 2
and the Zero-Clause BSD license.

ZERO-CLAUSE BSD LICENSE FOR CODE IN THE PYTHON DOCUMENTATION
 ----------------------------------------------------------------------

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

## Additional Assets

### Jetbrains Mono typeface

Redistributed under Apache License 2.0.

link: https://www.fontspace.com/jetbrains-mono-font-f44398

## McRogueFace Engine

Source code written by me is located in the `src` and `platform` directories.  

McRogueFace Engine: Copyright © 2023, John McCardle.

All rights reserved.

Published to publicly accessible git repositories for educational and collaborative purposes. I'll license this code when I feel like it is relatively stable and warrants supporting.
