# Third-Party Notices

This page identifies third-party material copied into generated DEAPack
Documentation. These notices apply only to the named third-party material.
They neither select nor grant a license for DEAPack's project-owned software,
Documentation, figures, or data.
No upstream author or project endorses or supports DEAPack merely because its
work is acknowledged here. License text inside fenced blocks is retained in
its upstream English form; localized narrative does not replace it.

## Audited build-surface inventory

| Component | Audited release-build version | Where it appears | Upstream terms |
|---|---:|---|---|
| Sphinx | 9.1.0 | Generated Documentation site assets | BSD-2-Clause |
| PyData Sphinx Theme | 0.19.0 | Generated site CSS, JavaScript, templates, and web assets | BSD-3-Clause |
| Sphinx Copybutton | 0.5.2 | Generated copy-control CSS, JavaScript, and SVG controls | MIT |
| ClipboardJS | 2.0.8, supplied by Sphinx Copybutton | Generated copy-to-clipboard JavaScript | MIT |
| Tabler Icons | Copy/check SVG controls supplied by Sphinx Copybutton 0.5.2 | Generated copy controls | MIT |
| Bootstrap | 5.3.3, supplied by the theme | Generated site CSS and JavaScript | MIT |
| Font Awesome Free | 7.2.0, supplied by the theme | Generated site code, icons, and webfonts | Code: MIT; icons: CC BY 4.0; fonts: SIL OFL 1.1 |
| Pygments | 2.20.0 | Generated syntax-highlighting stylesheet | BSD-2-Clause |
| MathJax | 4.0.0 | Loaded from the pinned jsDelivr URL at viewing time; not copied into the built site | Apache-2.0 |

The versions in this table are reviewed build baselines, not general runtime
requirements. A baseline name or upstream web page does not substitute for
the license notice shipped with the generated site.

## Sphinx 9.1.0 — BSD-2-Clause

The following notice is reproduced from Sphinx 9.1.0's `LICENSE.rst`:

```text
Copyright (c) 2007-2025 by the Sphinx team (see AUTHORS file).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## PyData Sphinx Theme 0.19.0 — BSD-3-Clause

The following notice is reproduced from the theme's `LICENSE` file:

```text
BSD 3-Clause License

Copyright (c) 2018, pandas
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Pygments 2.20.0 — BSD-2-Clause

The following notice is reproduced from Pygments 2.20.0's `LICENSE` file:

```text
Copyright (c) 2006-2022 by the respective authors (see AUTHORS file).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

## Copy controls, Bootstrap, and Font Awesome code — MIT

Sphinx Copybutton 0.5.2 is copyright 2018 Chris Holdgraf. Its bundled
ClipboardJS 2.0.8 asset is copyright Zeno Rocha, and its copy/check SVG
controls come from Tabler Icons, copyright 2020-2026 Paweł Kuna. Bootstrap
5.3.3 is copyright 2011-2024 The Bootstrap Authors. Font Awesome Free 7.2.0
code is copyright 2026 Fonticons, Inc. Each is distributed under the following
MIT License:

```text
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Font Awesome icons — CC BY 4.0

Font Awesome Free 7.2.0 icons are copyright 2026 Fonticons, Inc. and are
licensed under the
[Creative Commons Attribution 4.0 International license](https://creativecommons.org/licenses/by/4.0/legalcode).
The icons are supplied through PyData Sphinx Theme 0.19.0. DEAPack does not
alter the upstream icon data or claim authorship of it; selecting an icon for a
site control does not imply endorsement by Fonticons.

## Font Awesome webfonts — SIL OFL 1.1

Font Awesome Free 7.2.0 webfonts are copyright 2026 Fonticons, Inc. and are
licensed under the SIL Open Font License 1.1 reproduced below.

```text
SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007

PREAMBLE

The goals of the Open Font License (OFL) are to stimulate worldwide
development of collaborative font projects, to support the font creation
efforts of academic and linguistic communities, and to provide a free and
open framework in which fonts may be shared and improved in partnership with
others.

The OFL allows the licensed fonts to be used, studied, modified and
redistributed freely as long as they are not sold by themselves. The fonts,
including any derivative works, can be bundled, embedded, redistributed and/or
sold with any software provided that any reserved names are not used by
derivative works. The fonts and derivatives, however, cannot be released under
any other type of license. The requirement for fonts to remain under this
license does not apply to any document created using the fonts or their
derivatives.

DEFINITIONS

"Font Software" refers to the set of files released by the Copyright Holder(s)
under this license and clearly marked as such. This may include source files,
build scripts and documentation.

"Reserved Font Name" refers to any names specified as such after the copyright
statement(s).

"Original Version" refers to the collection of Font Software components as
distributed by the Copyright Holder(s).

"Modified Version" refers to any derivative made by adding to, deleting, or
substituting -- in part or in whole -- any of the components of the Original
Version, by changing formats or by porting the Font Software to a new
environment.

"Author" refers to any designer, engineer, programmer, technical writer or
other person who contributed to the Font Software.

PERMISSION & CONDITIONS

Permission is hereby granted, free of charge, to any person obtaining a copy of
the Font Software, to use, study, copy, merge, embed, modify, redistribute, and
sell modified and unmodified copies of the Font Software, subject to the
following conditions:

1) Neither the Font Software nor any of its individual components, in Original
or Modified Versions, may be sold by itself.

2) Original or Modified Versions of the Font Software may be bundled,
redistributed and/or sold with any software, provided that each copy contains
the above copyright notice and this license. These can be included either as
stand-alone text files, human-readable headers or in the appropriate
machine-readable metadata fields within text or binary files as long as those
fields can be easily viewed by the user.

3) No Modified Version of the Font Software may use the Reserved Font Name(s)
unless explicit written permission is granted by the corresponding Copyright
Holder. This restriction only applies to the primary font name as presented to
the users.

4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font Software
shall not be used to promote, endorse or advertise any Modified Version,
except to acknowledge the contribution(s) of the Copyright Holder(s) and the
Author(s) or with their explicit written permission.

5) The Font Software, modified or unmodified, in part or in whole, must be
distributed entirely under this license, and must not be distributed under any
other license. The requirement for fonts to remain under this license does not
apply to any document created using the Font Software.

TERMINATION

This license becomes null and void if any of the above conditions are not met.

DISCLAIMER

THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF COPYRIGHT, PATENT,
TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR
ANY CLAIM, DAMAGES OR OTHER LIABILITY, INCLUDING ANY GENERAL, SPECIAL,
INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF THE USE OR INABILITY TO USE
THE FONT SOFTWARE OR FROM OTHER DEALINGS IN THE FONT SOFTWARE.
```

## TeX Gyre Termes and Heros — GUST Font License

TeX Gyre's upstream font metadata and manifests identify the individual
copyright holders and the URW base fonts from which the families were derived.
The release build uses the fonts without renaming or claiming endorsement. The
GUST Font License supplied with the TeX Gyre distribution reads:

```text
This is version 1.0, dated 22 June 2009, of the GUST Font License.
(GUST is the Polish TeX Users Group, http://www.gust.org.pl)

For the most recent version of this license see
http://www.gust.org.pl/fonts/licenses/GUST-FONT-LICENSE.txt
or
http://tug.org/fonts/licenses/GUST-FONT-LICENSE.txt

This work may be distributed and/or modified under the conditions
of the LaTeX Project Public License, either version 1.3c of this
license or (at your option) any later version.

Please also observe the following clause:
1) it is requested, but not legally required, that derived works be
   distributed only after changing the names of the fonts comprising this
   work and given in an accompanying "manifest", and that the
   files comprising the Work, as listed in the manifest, also be given
   new names. Any exceptions to this request are also given in the
   manifest.

   We recommend the manifest be given in a separate file named
   MANIFEST-<fontid>.txt, where <fontid> is some unique identification
   of the font family. If a separate "readme" file accompanies the Work,
   we recommend a name of the form README-<fontid>.txt.

The latest version of the LaTeX Project Public License is in
http://www.latex-project.org/lppl.txt and version 1.3c or later
is part of all distributions of LaTeX version 2006/05/20 or later.
```

## LPPL 1.3c — `fncychap` and TeX Gyre license basis

The unmodified LPPL 1.3c text follows. It applies only to the third-party
works identified above, not to unrelated DEAPack project-owned components.

```text
The LaTeX Project Public License
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

LPPL Version 1.3c  2008-05-04

Copyright 1999 2002-2008 LaTeX3 Project
    Everyone is allowed to distribute verbatim copies of this
    license document, but modification of it is not allowed.


PREAMBLE
========

The LaTeX Project Public License (LPPL) is the primary license under
which the LaTeX kernel and the base LaTeX packages are distributed.

You may use this license for any work of which you hold the copyright
and which you wish to distribute.  This license may be particularly
suitable if your work is TeX-related (such as a LaTeX package), but
it is written in such a way that you can use it even if your work is
unrelated to TeX.

The section `WHETHER AND HOW TO DISTRIBUTE WORKS UNDER THIS LICENSE',
below, gives instructions, examples, and recommendations for authors
who are considering distributing their works under this license.

This license gives conditions under which a work may be distributed
and modified, as well as conditions under which modified versions of
that work may be distributed.

We, the LaTeX3 Project, believe that the conditions below give you
the freedom to make and distribute modified versions of your work
that conform with whatever technical specifications you wish while
maintaining the availability, integrity, and reliability of
that work.  If you do not see how to achieve your goal while
meeting these conditions, then read the document `cfgguide.tex'
and `modguide.tex' in the base LaTeX distribution for suggestions.


DEFINITIONS
===========

In this license document the following terms are used:

   `Work'
    Any work being distributed under this License.

   `Derived Work'
    Any work that under any applicable law is derived from the Work.

   `Modification'
    Any procedure that produces a Derived Work under any applicable
    law -- for example, the production of a file containing an
    original file associated with the Work or a significant portion of
    such a file, either verbatim or with modifications and/or
    translated into another language.

   `Modify'
    To apply any procedure that produces a Derived Work under any
    applicable law.

   `Distribution'
    Making copies of the Work available from one person to another, in
    whole or in part.  Distribution includes (but is not limited to)
    making any electronic components of the Work accessible by
    file transfer protocols such as FTP or HTTP or by shared file
    systems such as Sun's Network File System (NFS).

   `Compiled Work'
    A version of the Work that has been processed into a form where it
    is directly usable on a computer system.  This processing may
    include using installation facilities provided by the Work,
    transformations of the Work, copying of components of the Work, or
    other activities.  Note that modification of any installation
    facilities provided by the Work constitutes modification of the Work.

   `Current Maintainer'
    A person or persons nominated as such within the Work.  If there is
    no such explicit nomination then it is the `Copyright Holder' under
    any applicable law.

   `Base Interpreter'
    A program or process that is normally needed for running or
    interpreting a part or the whole of the Work.

    A Base Interpreter may depend on external components but these
    are not considered part of the Base Interpreter provided that each
    external component clearly identifies itself whenever it is used
    interactively.  Unless explicitly specified when applying the
    license to the Work, the only applicable Base Interpreter is a
    `LaTeX-Format' or in the case of files belonging to the
    `LaTeX-format' a program implementing the `TeX language'.



CONDITIONS ON DISTRIBUTION AND MODIFICATION
===========================================

1.  Activities other than distribution and/or modification of the Work
are not covered by this license; they are outside its scope.  In
particular, the act of running the Work is not restricted and no
requirements are made concerning any offers of support for the Work.

2.  You may distribute a complete, unmodified copy of the Work as you
received it.  Distribution of only part of the Work is considered
modification of the Work, and no right to distribute such a Derived
Work may be assumed under the terms of this clause.

3.  You may distribute a Compiled Work that has been generated from a
complete, unmodified copy of the Work as distributed under Clause 2
above, as long as that Compiled Work is distributed in such a way that
the recipients may install the Compiled Work on their system exactly
as it would have been installed if they generated a Compiled Work
directly from the Work.

4.  If you are the Current Maintainer of the Work, you may, without
restriction, modify the Work, thus creating a Derived Work.  You may
also distribute the Derived Work without restriction, including
Compiled Works generated from the Derived Work.  Derived Works
distributed in this manner by the Current Maintainer are considered to
be updated versions of the Work.

5.  If you are not the Current Maintainer of the Work, you may modify
your copy of the Work, thus creating a Derived Work based on the Work,
and compile this Derived Work, thus creating a Compiled Work based on
the Derived Work.

6.  If you are not the Current Maintainer of the Work, you may
distribute a Derived Work provided the following conditions are met
for every component of the Work unless that component clearly states
in the copyright notice that it is exempt from that condition.  Only
the Current Maintainer is allowed to add such statements of exemption
to a component of the Work.

  a. If a component of this Derived Work can be a direct replacement
     for a component of the Work when that component is used with the
     Base Interpreter, then, wherever this component of the Work
     identifies itself to the user when used interactively with that
     Base Interpreter, the replacement component of this Derived Work
     clearly and unambiguously identifies itself as a modified version
     of this component to the user when used interactively with that
     Base Interpreter.

  b. Every component of the Derived Work contains prominent notices
     detailing the nature of the changes to that component, or a
     prominent reference to another file that is distributed as part
     of the Derived Work and that contains a complete and accurate log
     of the changes.

  c. No information in the Derived Work implies that any persons,
     including (but not limited to) the authors of the original version
     of the Work, provide any support, including (but not limited to)
     the reporting and handling of errors, to recipients of the
     Derived Work unless those persons have stated explicitly that
     they do provide such support for the Derived Work.

  d. You distribute at least one of the following with the Derived Work:

       1. A complete, unmodified copy of the Work;
          if your distribution of a modified component is made by
          offering access to copy the modified component from a
          designated place, then offering equivalent access to copy
          the Work from the same or some similar place meets this
          condition, even though third parties are not compelled to
          copy the Work along with the modified component;

       2. Information that is sufficient to obtain a complete,
          unmodified copy of the Work.

7.  If you are not the Current Maintainer of the Work, you may
distribute a Compiled Work generated from a Derived Work, as long as
the Derived Work is distributed to all recipients of the Compiled
Work, and as long as the conditions of Clause 6, above, are met with
regard to the Derived Work.

8.  The conditions above are not intended to prohibit, and hence do not
apply to, the modification, by any method, of any component so that it
becomes identical to an updated version of that component of the Work as
it is distributed by the Current Maintainer under Clause 4, above.

9.  Distribution of the Work or any Derived Work in an alternative
format, where the Work or that Derived Work (in whole or in part) is
then produced by applying some process to that format, does not relax or
nullify any sections of this license as they pertain to the results of
applying that process.

10. a. A Derived Work may be distributed under a different license
       provided that license itself honors the conditions listed in
       Clause 6 above, in regard to the Work, though it does not have
       to honor the rest of the conditions in this license.

    b. If a Derived Work is distributed under a different license, that
       Derived Work must provide sufficient documentation as part of
       itself to allow each recipient of that Derived Work to honor the
       restrictions in Clause 6 above, concerning changes from the Work.

11. This license places no restrictions on works that are unrelated to
the Work, nor does this license place any restrictions on aggregating
such works with the Work by any means.

12.  Nothing in this license is intended to, or may be used to, prevent
complete compliance by all parties with all applicable laws.


NO WARRANTY
===========

There is no warranty for the Work.  Except when otherwise stated in
writing, the Copyright Holder provides the Work `as is', without
warranty of any kind, either expressed or implied, including, but not
limited to, the implied warranties of merchantability and fitness for a
particular purpose.  The entire risk as to the quality and performance
of the Work is with you.  Should the Work prove defective, you assume
the cost of all necessary servicing, repair, or correction.

In no event unless required by applicable law or agreed to in writing
will The Copyright Holder, or any author named in the components of the
Work, or any other party who may distribute and/or modify the Work as
permitted above, be liable to you for damages, including any general,
special, incidental or consequential damages arising out of any use of
the Work or out of inability to use the Work (including, but not limited
to, loss of data, data being rendered inaccurate, or losses sustained by
anyone as a result of any failure of the Work to operate with any other
programs), even if the Copyright Holder or said author or said other
party has been advised of the possibility of such damages.


MAINTENANCE OF THE WORK
=======================

The Work has the status `author-maintained' if the Copyright Holder
explicitly and prominently states near the primary copyright notice in
the Work that the Work can only be maintained by the Copyright Holder
or simply that it is `author-maintained'.

The Work has the status `maintained' if there is a Current Maintainer
who has indicated in the Work that they are willing to receive error
reports for the Work (for example, by supplying a valid e-mail
address). It is not required for the Current Maintainer to acknowledge
or act upon these error reports.

The Work changes from status `maintained' to `unmaintained' if there
is no Current Maintainer, or the person stated to be Current
Maintainer of the work cannot be reached through the indicated means
of communication for a period of six months, and there are no other
significant signs of active maintenance.

You can become the Current Maintainer of the Work by agreement with
any existing Current Maintainer to take over this role.

If the Work is unmaintained, you can become the Current Maintainer of
the Work through the following steps:

 1.  Make a reasonable attempt to trace the Current Maintainer (and
     the Copyright Holder, if the two differ) through the means of
     an Internet or similar search.

 2.  If this search is successful, then enquire whether the Work
     is still maintained.

  a. If it is being maintained, then ask the Current Maintainer
     to update their communication data within one month.

  b. If the search is unsuccessful or no action to resume active
     maintenance is taken by the Current Maintainer, then announce
     within the pertinent community your intention to take over
     maintenance.  (If the Work is a LaTeX work, this could be
     done, for example, by posting to comp.text.tex.)

 3a. If the Current Maintainer is reachable and agrees to pass
     maintenance of the Work to you, then this takes effect
     immediately upon announcement.

  b. If the Current Maintainer is not reachable and the Copyright
     Holder agrees that maintenance of the Work be passed to you,
     then this takes effect immediately upon announcement.

 4.  If you make an `intention announcement' as described in 2b. above
     and after three months your intention is challenged neither by
     the Current Maintainer nor by the Copyright Holder nor by other
     people, then you may arrange for the Work to be changed so as
     to name you as the (new) Current Maintainer.

 5.  If the previously unreachable Current Maintainer becomes
     reachable once more within three months of a change completed
     under the terms of 3b) or 4), then that Current Maintainer must
     become or remain the Current Maintainer upon request provided
     they then update their communication data within one month.

A change in the Current Maintainer does not, of itself, alter the fact
that the Work is distributed under the LPPL license.

If you become the Current Maintainer of the Work, you should
immediately provide, within the Work, a prominent and unambiguous
statement of your status as Current Maintainer.  You should also
announce your new status to the same pertinent community as
in 2b) above.


WHETHER AND HOW TO DISTRIBUTE WORKS UNDER THIS LICENSE
======================================================

This section contains important instructions, examples, and
recommendations for authors who are considering distributing their
works under this license.  These authors are addressed as `you' in
this section.

Choosing This License or Another License
----------------------------------------

If for any part of your work you want or need to use *distribution*
conditions that differ significantly from those in this license, then
do not refer to this license anywhere in your work but, instead,
distribute your work under a different license.  You may use the text
of this license as a model for your own license, but your license
should not refer to the LPPL or otherwise give the impression that
your work is distributed under the LPPL.

The document `modguide.tex' in the base LaTeX distribution explains
the motivation behind the conditions of this license.  It explains,
for example, why distributing LaTeX under the GNU General Public
License (GPL) was considered inappropriate.  Even if your work is
unrelated to LaTeX, the discussion in `modguide.tex' may still be
relevant, and authors intending to distribute their works under any
license are encouraged to read it.

A Recommendation on Modification Without Distribution
-----------------------------------------------------

It is wise never to modify a component of the Work, even for your own
personal use, without also meeting the above conditions for
distributing the modified component.  While you might intend that such
modifications will never be distributed, often this will happen by
accident -- you may forget that you have modified that component; or
it may not occur to you when allowing others to access the modified
version that you are thus distributing it and violating the conditions
of this license in ways that could have legal implications and, worse,
cause problems for the community.  It is therefore usually in your
best interest to keep your copy of the Work identical with the public
one.  Many works provide ways to control the behavior of that work
without altering any of its licensed components.

How to Use This License
-----------------------

To use this license, place in each of the components of your work both
an explicit copyright notice including your name and the year the work
was authored and/or last substantially modified.  Include also a
statement that the distribution and/or modification of that component
is constrained by the conditions in this license.

Here is an example of such a notice and statement:

  %% pig.dtx
  %% Copyright 2008 M. Y. Name
  %
  % This work may be distributed and/or modified under the
  % conditions of the LaTeX Project Public License, either version 1.3
  % of this license or (at your option) any later version.
  % The latest version of this license is in
  %   https://www.latex-project.org/lppl.txt
  % and version 1.3c or later is part of all distributions of LaTeX
  % version 2008 or later.
  %
  % This work has the LPPL maintenance status `maintained'.
  %
  % The Current Maintainer of this work is M. Y. Name.
  %
  % This work consists of the files pig.dtx and pig.ins
  % and the derived file pig.sty.

Given such a notice and statement in a file, the conditions
given in this license document would apply, with the `Work' referring
to the three files `pig.dtx', `pig.ins', and `pig.sty' (the last being
generated from `pig.dtx' using `pig.ins'), the `Base Interpreter'
referring to any `LaTeX-Format', and both `Copyright Holder' and
`Current Maintainer' referring to the person `M. Y. Name'.

If you do not want the Maintenance section of LPPL to apply to your
Work, change `maintained' above into `author-maintained'.
However, we recommend that you use `maintained', as the Maintenance
section was added in order to ensure that your Work remains useful to
the community even when you can no longer maintain and support it
yourself.

Derived Works That Are Not Replacements
---------------------------------------

Several clauses of the LPPL specify means to provide reliability and
stability for the user community. They therefore concern themselves
with the case that a Derived Work is intended to be used as a
(compatible or incompatible) replacement of the original Work. If
this is not the case (e.g., if a few lines of code are reused for a
completely different task), then clauses 6b and 6d shall not apply.


Important Recommendations
-------------------------

 Defining What Constitutes the Work

   The LPPL requires that distributions of the Work contain all the
   files of the Work.  It is therefore important that you provide a
   way for the licensee to determine which files constitute the Work.
   This could, for example, be achieved by explicitly listing all the
   files of the Work near the copyright notice of each file or by
   using a line such as:

    % This work consists of all files listed in manifest.txt.

   in that place.  In the absence of an unequivocal list it might be
   impossible for the licensee to determine what is considered by you
   to comprise the Work and, in such a case, the licensee would be
   entitled to make reasonable conjectures as to which files comprise
   the Work.
```

## DejaVu Sans and Sans Mono — retained font notices

The substantive DejaVu notice distributed with Matplotlib 3.11.1 is reproduced
below with whitespace normalized and its non-substantive RCS trailer omitted.
The historical notice is retained for vector assets produced with DejaVu.

```text
Fonts are (c) Bitstream (see below). DejaVu changes are in public domain.
Glyphs imported from Arev fonts are (c) Tavmjong Bah (see below)

Bitstream Vera Fonts Copyright
------------------------------

Copyright (c) 2003 by Bitstream, Inc. All Rights Reserved. Bitstream Vera is
a trademark of Bitstream, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of the fonts accompanying this license ("Fonts") and associated
documentation files (the "Font Software"), to reproduce and distribute the
Font Software, including without limitation the rights to use, copy, merge,
publish, distribute, and/or sell copies of the Font Software, and to permit
persons to whom the Font Software is furnished to do so, subject to the
following conditions:

The above copyright and trademark notices and this permission notice shall
be included in all copies of one or more of the Font Software typefaces.

The Font Software may be modified, altered, or added to, and in particular
the designs of glyphs or characters in the Fonts may be modified and
additional glyphs or characters may be added to the Fonts, only if the fonts
are renamed to names not containing either the words "Bitstream" or the word
"Vera".

This License becomes null and void to the extent applicable to Fonts or Font
Software that has been modified and is distributed under the "Bitstream
Vera" names.

The Font Software may be sold as part of a larger software package but no
copy of one or more of the Font Software typefaces may be sold by itself.

THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT OF COPYRIGHT, PATENT,
TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL BITSTREAM OR THE GNOME
FOUNDATION BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, INCLUDING
ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF
THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM OTHER DEALINGS IN THE
FONT SOFTWARE.

Except as contained in this notice, the names of Gnome, the Gnome
Foundation, and Bitstream Inc., shall not be used in advertising or
otherwise to promote the sale, use or other dealings in this Font Software
without prior written authorization from the Gnome Foundation or Bitstream
Inc., respectively. For further information, contact: fonts at gnome dot
org.

Arev Fonts Copyright
--------------------

Copyright (c) 2006 by Tavmjong Bah. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining
a copy of the fonts accompanying this license ("Fonts") and
associated documentation files (the "Font Software"), to reproduce
and distribute the modifications to the Bitstream Vera Font Software,
including without limitation the rights to use, copy, merge, publish,
distribute, and/or sell copies of the Font Software, and to permit
persons to whom the Font Software is furnished to do so, subject to
the following conditions:

The above copyright and trademark notices and this permission notice
shall be included in all copies of one or more of the Font Software
typefaces.

The Font Software may be modified, altered, or added to, and in
particular the designs of glyphs or characters in the Fonts may be
modified and additional glyphs or characters may be added to the
Fonts, only if the fonts are renamed to names not containing either
the words "Tavmjong Bah" or the word "Arev".

This License becomes null and void to the extent applicable to Fonts
or Font Software that has been modified and is distributed under the
"Tavmjong Bah Arev" names.

The Font Software may be sold as part of a larger software package but
no copy of one or more of the Font Software typefaces may be sold by
itself.

THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL
TAVMJONG BAH BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM
OTHER DEALINGS IN THE FONT SOFTWARE.

Except as contained in this notice, the name of Tavmjong Bah shall not
be used in advertising or otherwise to promote the sale, use or other
dealings in this Font Software without prior written authorization
from Tavmjong Bah. For further information, contact: tavmjong @ free
. fr.
```

## Primary upstream evidence

The release review used the license files installed with the exact audited
Python distributions and the following primary upstream sources:

- [Sphinx 9.1.0 source and license](https://github.com/sphinx-doc/sphinx/tree/v9.1.0)
- [PyData Sphinx Theme 0.19.0 source and license](https://github.com/pydata/pydata-sphinx-theme/tree/v0.19.0)
- [Bootstrap 5.3.3 source and license](https://github.com/twbs/bootstrap/tree/v5.3.3)
- [Font Awesome Free 7.2.0 source and license](https://github.com/FortAwesome/Font-Awesome/tree/7.2.0)
- [Pygments 2.20.0 source and license](https://github.com/pygments/pygments/tree/2.20.0)
- [MathJax 4.0.0 source and license](https://github.com/mathjax/MathJax-src/tree/4.0.0)
- [`fncychap` 1.34 and its README at CTAN](https://ctan.org/tex-archive/macros/latex/contrib/fncychap)
- [LPPL 1.3c from the LaTeX Project](https://www.latex-project.org/lppl/lppl-1-3c/)
- [Noto CJK source and SIL OFL 1.1](https://github.com/notofonts/noto-cjk)
- [TeX Gyre source](https://ctan.org/pkg/tex-gyre) and [GUST Font License 1.0](https://ctan.org/license/gfl)
- [DejaVu Fonts license](https://dejavu-fonts.github.io/License.html)
- [Ubuntu 24.04 `fonts-noto-cjk`](https://packages.ubuntu.com/noble/fonts-noto-cjk), [`fonts-texgyre`](https://packages.ubuntu.com/noble/fonts-texgyre), and [`fonts-dejavu-mono`](https://packages.ubuntu.com/noble/fonts-dejavu-mono) package records
