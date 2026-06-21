from opendbc.car.tesla.values import CarControllerParams

# DAS_accState values for active stock longitudinal control
STOCK_ACTIVE_ACC_STATES = {3, 4}  # ACC_HOLD, ACC_ON


class StockLongPassthrough:
  def __init__(self):
    self.active = False
    self.exit_hold_counter = 0
    self.start_long_frame = 0
    self.just_exited = False
    self.long_frame = 0

  def update(self, op_accel: float, das_control: dict | None, cancel: bool, long_active: bool) -> bool:
    self.just_exited = False
    self.long_frame += 1

    if das_control is None or cancel or not long_active:
      if self.active:
        self._exit()
      return False

    stock_accel = das_control["DAS_accelMin"]
    stock_acc_state = das_control["DAS_accState"]
    stock_aeb = das_control["DAS_aebEvent"] == 1
    stock_active = stock_acc_state in STOCK_ACTIVE_ACC_STATES

    if stock_aeb:
      self.active = True
      return True

    if self.active:
      max_frames = int(CarControllerParams.STOCK_BRAKE_MAX_PASSTHROUGH_SEC * CarControllerParams.STOCK_BRAKE_LONG_HZ)
      if self.long_frame - self.start_long_frame > max_frames:
        self._exit()
        return False

      if stock_accel >= op_accel - CarControllerParams.STOCK_BRAKE_EXIT_TOLERANCE:
        self.exit_hold_counter += 1
        if self.exit_hold_counter >= CarControllerParams.STOCK_BRAKE_EXIT_HOLD_FRAMES:
          self._exit()
          return False
      else:
        self.exit_hold_counter = 0
      return True

    if (stock_active and
        stock_accel < -CarControllerParams.STOCK_BRAKE_MIN_DECEL and
        stock_accel < op_accel - CarControllerParams.STOCK_BRAKE_ENTER_TOLERANCE):
      self.active = True
      self.start_long_frame = self.long_frame
      self.exit_hold_counter = 0
      return True

    return False

  def _exit(self):
    self.active = False
    self.just_exited = True
    self.exit_hold_counter = 0
