package com.android.server.policy;

import android.view.KeyEvent;

class test_t110_navigation {
    public static void main(String[] args) {
        int[] nav = {KeyEvent.KEYCODE_HOME, KeyEvent.KEYCODE_MOVE_HOME,
                KeyEvent.KEYCODE_MENU, KeyEvent.KEYCODE_APP_SWITCH, KeyEvent.KEYCODE_BACK};
        for (String name : new String[]{"gpio-keys", "sec_touchscreen"}) {
            for (int key : nav) {
                assert T110NavigationKeys.shouldSuppress(true, name, false, key);
                assert !T110NavigationKeys.shouldSuppress(false, name, false, key);
                assert !T110NavigationKeys.shouldSuppress(true, name, true, key);
            }
            for (int key : new int[]{KeyEvent.KEYCODE_POWER, KeyEvent.KEYCODE_VOLUME_UP,
                    KeyEvent.KEYCODE_VOLUME_DOWN, KeyEvent.KEYCODE_UNKNOWN}) {
                assert !T110NavigationKeys.shouldSuppress(true, name, false, key);
            }
        }
        for (int key : nav) {
            for (String name : new String[]{null, "Virtual", "USB Keyboard", "88pm822_on"}) {
                assert !T110NavigationKeys.shouldSuppress(true, name, false, key);
            }
        }
        System.out.println("T110_NAVIGATION_MODE_FILTER_PASS");
    }
}
