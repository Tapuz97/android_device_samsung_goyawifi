package com.android.server.policy;

import android.view.KeyEvent;

/** Suppress only the T110's built-in navigation buttons, never its touch stream. */
final class T110NavigationKeys {
    static boolean shouldSuppress(boolean touchNavigation, String deviceName,
            boolean virtualDevice, int keyCode) {
        if (!touchNavigation || virtualDevice) return false;
        if (!"gpio-keys".equals(deviceName) && !"sec_touchscreen".equals(deviceName)) {
            return false;
        }
        return keyCode == KeyEvent.KEYCODE_HOME || keyCode == KeyEvent.KEYCODE_MOVE_HOME
                || keyCode == KeyEvent.KEYCODE_BACK || keyCode == KeyEvent.KEYCODE_MENU
                || keyCode == KeyEvent.KEYCODE_APP_SWITCH;
    }
}
