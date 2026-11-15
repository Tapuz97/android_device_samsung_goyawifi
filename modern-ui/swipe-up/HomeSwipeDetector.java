/* Copyright 2026. Licensed under the Apache License, Version 2.0. */
package com.android.launcher3.util;

/** Gesture recognition only; Android dispatch and launcher state stay in DragLayer. */
public final class HomeSwipeDetector {
    private final float mDistance, mSlop;
    private final long mLongPressTimeout;
    private float mDownX, mDownY;
    private long mDownTime;
    private boolean mEligible, mMoved, mClaimed;

    public HomeSwipeDetector(float distance, float slop, long longPressTimeout) {
        mDistance = distance;
        mSlop = slop;
        mLongPressTimeout = longPressTimeout;
    }

    public void begin(float x, float y, long time, boolean eligible) {
        mDownX = x;
        mDownY = y;
        mDownTime = time;
        mEligible = eligible;
        mMoved = mClaimed = false;
    }

    public void cancel() {
        mEligible = mMoved = mClaimed = false;
    }

    public boolean isTracking() {
        return mEligible;
    }

    public boolean move(float x, float y, long time, int pointers) {
        if (!mEligible || pointers != 1) {
            cancel();
            return false;
        }
        if (mClaimed) return true;
        if (!mMoved && time - mDownTime >= mLongPressTimeout) {
            cancel();
            return false;
        }
        float dx = Math.abs(x - mDownX);
        float up = mDownY - y;
        if (Math.max(dx, Math.abs(up)) <= mSlop) return false;
        mMoved = true;
        // Never steal a sequence once it chooses another direction.
        if (up < -mSlop || dx * 1.5f >= Math.abs(up)) {
            cancel();
            return false;
        }
        if (up >= mDistance) mClaimed = true;
        return mClaimed;
    }

    public boolean end(float x, float y, int pointers) {
        float up = mDownY - y;
        boolean open = mEligible && mClaimed && pointers == 1
                && up >= mDistance && up > Math.abs(x - mDownX) * 1.5f;
        cancel();
        return open;
    }
}
