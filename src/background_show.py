import math
from direct.task import Task

class BackgroundShow:
    """Menu camera orbit around the main chessboard."""

    ORBIT_TASK = "bgShowOrbit"

    def __init__(self, base):
        self.base = base
        self._visible = False
        self._tasks_on = False

    def show(self):
        self._visible = True
        self._start_tasks()

    def hide(self):
        self._visible = False
        self._stop_tasks()

    def _start_tasks(self):
        if self._tasks_on:
            return
        self._tasks_on = True
        self.base.taskMgr.add(self._orbit_update, self.ORBIT_TASK)

    def _stop_tasks(self):
        if not self._tasks_on:
            return
        self._tasks_on = False
        self.base.taskMgr.remove(self.ORBIT_TASK)

    def _orbit_update(self, task):
        t = task.time
        if not self._visible:
            return Task.cont
        ang = math.radians(t * 5.0)  # Slow cinematic rotation
        radius = 15.0
        # Slowly orbit around the board at a nice viewing angle
        self.base.camera.setPos(
            math.sin(ang) * radius,
            math.cos(ang) * radius,
            8.0 + math.sin(t * 0.4) * 1.5,
        )
        self.base.camera.lookAt(0, 0, 0)
        return Task.cont

    def destroy(self):
        self._stop_tasks()
