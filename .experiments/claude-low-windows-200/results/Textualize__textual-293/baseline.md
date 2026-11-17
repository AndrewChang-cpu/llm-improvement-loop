Tabs

## Example

The video below shows a few different features:

* Clicking on the underline or anywhere on the bar will activate the nearest tab.
* Using "left" and "right" arrows on the keyboard will cycle through tabs, wrapping around 
* Pressing a number key will cause the tab with that number to activate
* Pressing a letter will "search" through tab labels, so when I press "M" key, it jumps to "March" to "May". It is cycling through tabs that begin with the letter "M".

https://user-images.githubusercontent.com/5740731/154511136-d26e1ff2-ec16-4047-b05f-4ecad4cc90b9.mov

## Demo

See the demo in the `sandbox` dir: `python -m tabs` - or watch [the video](https://www.youtube.com/watch?v=59CVt9gVcvo).

Screenshot of the demo:
![image](https://user-images.githubusercontent.com/5740731/154489480-24a93ff6-d14e-4a10-a365-7c6571b401d0.png)

When there are no tabs, only the "inactive" underline renders:
![image](https://user-images.githubusercontent.com/5740731/154468393-bf5a4270-68c5-49b5-8ac0-990410237834.png)

## Outstanding tasks

- [x] Increase tab click target to include padding
- [x] Handle case where user supplies no tabs - just render inactive underline
- [x] Increase tab click target to include underline area
- [x] Widget-level keyboard control
- [x] Minor rounding error fix
- [x] Docstrings