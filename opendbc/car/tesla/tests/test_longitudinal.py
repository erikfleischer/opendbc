import unittest

from opendbc.car.tesla.longitudinal import StockLongPassthrough
from opendbc.car.tesla.values import CarControllerParams


def _das_control(accel_min, acc_state=4, aeb_event=0):
  return {
    "DAS_accelMin": accel_min,
    "DAS_accState": acc_state,
    "DAS_aebEvent": aeb_event,
    "DAS_controlCounter": 0,
  }


class TestStockLongPassthrough(unittest.TestCase):
  def setUp(self):
    self.passthrough = StockLongPassthrough()

  def test_enter_when_stock_brakes_harder(self):
    active = self.passthrough.update(-0.5, _das_control(-2.0), cancel=False, long_active=True)
    self.assertTrue(active)
    self.assertTrue(self.passthrough.active)

  def test_no_enter_within_tolerance(self):
    active = self.passthrough.update(-0.5, _das_control(-0.6), cancel=False, long_active=True)
    self.assertFalse(active)

  def test_no_enter_without_active_stock_acc(self):
    active = self.passthrough.update(-0.5, _das_control(-2.0, acc_state=0), cancel=False, long_active=True)
    self.assertFalse(active)

  def test_no_enter_below_min_decel(self):
    active = self.passthrough.update(0.0, _das_control(-0.1), cancel=False, long_active=True)
    self.assertFalse(active)

  def test_enter_on_stock_aeb(self):
    active = self.passthrough.update(0.0, _das_control(0.0, aeb_event=1), cancel=False, long_active=True)
    self.assertTrue(active)

  def test_exit_after_hold(self):
    self.passthrough.update(-0.5, _das_control(-2.0), cancel=False, long_active=True)
    hold_frames = CarControllerParams.STOCK_BRAKE_EXIT_HOLD_FRAMES
    for _ in range(hold_frames - 1):
      self.assertTrue(self.passthrough.update(-0.5, _das_control(-0.3), cancel=False, long_active=True))
      self.assertFalse(self.passthrough.just_exited)
    active = self.passthrough.update(-0.5, _das_control(-0.3), cancel=False, long_active=True)
    self.assertFalse(active)
    self.assertTrue(self.passthrough.just_exited)

  def test_cancel_clears_passthrough(self):
    self.passthrough.update(-0.5, _das_control(-2.0), cancel=False, long_active=True)
    active = self.passthrough.update(-0.5, _das_control(-2.0), cancel=True, long_active=True)
    self.assertFalse(active)
    self.assertFalse(self.passthrough.active)

  def test_disengage_clears_passthrough(self):
    self.passthrough.update(-0.5, _das_control(-2.0), cancel=False, long_active=True)
    active = self.passthrough.update(-0.5, _das_control(-2.0), cancel=False, long_active=False)
    self.assertFalse(active)
    self.assertFalse(self.passthrough.active)

  def test_timeout_forces_exit(self):
    self.passthrough.update(-0.5, _das_control(-2.0), cancel=False, long_active=True)
    max_frames = int(CarControllerParams.STOCK_BRAKE_MAX_PASSTHROUGH_SEC * CarControllerParams.STOCK_BRAKE_LONG_HZ)
    for _ in range(max_frames):
      self.passthrough.update(-0.5, _das_control(-2.0), cancel=False, long_active=True)
    active = self.passthrough.update(-0.5, _das_control(-2.0), cancel=False, long_active=True)
    self.assertFalse(active)
    self.assertTrue(self.passthrough.just_exited)


if __name__ == "__main__":
  unittest.main()
