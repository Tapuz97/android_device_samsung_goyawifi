/*
 * Copyright (C) 2026 The LineageOS Project
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy at http://www.apache.org/licenses/LICENSE-2.0
 */
package com.android.server.policy;

import android.view.KeyEvent;

/** Board key suppression for a touchscreen shared with capacitive navigation. */
final class PhysicalNavigationKeyPolicy {
    private PhysicalNavigationKeyPolicy() { }

    static boolean shouldSuppress(String deviceName, int keyCode, int deviceId,
            boolean injected, boolean virtualKey) {
        if (injected || virtualKey || deviceId < 0) {
            return false;
        }
        if (!"gpio-keys".equals(deviceName) && !"sec_touchscreen".equals(deviceName)) {
            return false;
        }
        return keyCode == KeyEvent.KEYCODE_HOME || keyCode == KeyEvent.KEYCODE_BACK
                || keyCode == KeyEvent.KEYCODE_APP_SWITCH || keyCode == KeyEvent.KEYCODE_MENU;
    }
}
