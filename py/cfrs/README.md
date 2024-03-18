# CFRS

This is an implementation of [CFRS](https://github.com/susam/cfrs), an "extremely minimal drawing language".

This is built with [pygame](https://www.pygame.org/). Make sure it is installed first.

## Usage

`python -m cfrs $code`

For example, to show [demo #0](https://susam.net/cfrs.html#0),
`python -m cfrs "[[[[[[[[[[[[[[[FF]]]]]]]SRRF[RRR]]]]]]C]]]"`

When the window is opened, press space to pause/resume (if still drawing), or press `q` to quit.

## NOTE

Currently,
* pixels are drawn one-by-one. This means that code without `S` are not drawn instantly but still animated (usually at a faster rate than `S`)
* wait to quit at 10 fps after drawing halted

