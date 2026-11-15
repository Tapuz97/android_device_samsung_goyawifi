package com.android.launcher3.util;

public final class HomeSwipeDetectorTest {
    private static int checks;
    private static void check(boolean condition, String name) {
        checks++;
        if (!condition) throw new AssertionError(name);
    }
    private static HomeSwipeDetector start(boolean eligible) {
        HomeSwipeDetector d = new HomeSwipeDetector(48, 8, 500);
        d.begin(100, 200, 0, eligible);
        return d;
    }
    public static void main(String[] args) {
        HomeSwipeDetector d = start(true);
        check(d.move(104, 140, 100, 1), "clear upward swipe");
        check(d.end(105, 120, 1), "open on release");
        check(!d.end(105, 120, 1), "only open once");
        d = start(true);
        check(!d.end(100, 200, 1), "tap stays tap");
        check(!start(true).move(102, 197, 40, 1), "jitter ignored");
        check(!start(true).move(100, 170, 100, 1), "short drag ignored");
        d = start(true);
        check(!d.move(160, 190, 100, 1), "horizontal paging preserved");
        check(!d.move(100, 100, 160, 1), "cannot steal after horizontal");
        d = start(true);
        check(!d.move(101, 240, 100, 1), "downward swipe preserved");
        check(!d.move(100, 100, 160, 1), "cannot steal after downward");
        check(!start(true).move(145, 150, 100, 1), "diagonal rejected");
        check(!start(true).move(100, 130, 600, 1), "held icon preserved");
        check(!start(false).move(100, 100, 100, 1), "widget/non-home excluded");
        d = start(true);
        check(!d.move(100, 100, 100, 2), "pinch rejected");
        check(!d.end(100, 100, 1), "pinch cannot become swipe");
        d = start(true);
        check(d.move(100, 140, 100, 1), "claim before cancel");
        d.cancel();
        check(!d.end(100, 100, 1), "cancel never opens");
        d = start(true);
        d.move(100, 140, 100, 1);
        check(!d.end(100, 180, 1), "reversal does not open");
        d = start(true);
        d.move(100, 185, 100, 1);
        check(d.move(102, 140, 900, 1), "slow deliberate motion");
        check(d.end(102, 120, 1), "slow swipe release");
        d = start(true);
        d.move(100, 140, 100, 1);
        d.move(100, 100, 110, 2);
        check(!d.end(100, 100, 1), "multi-touch after interception cancels");
        // The Apps drawer passes -Y to the same detector.
        d = new HomeSwipeDetector(48, 8, 500);
        d.begin(100, -200, 0, true);
        check(d.move(104, -260, 100, 1), "drawer downward claim");
        check(d.end(105, -300, 1), "drawer downward dismissal");
        d.begin(100, -200, 0, true);
        check(!d.move(100, -140, 100, 1), "drawer upward scroll preserved");
        check(!d.end(100, -100, 1), "upward never dismisses");
        d.begin(100, -200, 0, false);
        check(!d.move(100, -280, 100, 1), "scrolled list cannot dismiss");
        d.begin(100, -200, 0, true);
        check(!d.move(160, -210, 100, 1), "drawer horizontal rejected");
        d.begin(100, -200, 0, true);
        check(!d.move(100, -280, 700, 1), "drawer long press preserved");
        d.begin(100, -200, 0, true);
        check(!d.move(100, -280, 100, 2), "drawer multi-touch preserved");
        System.out.println("PASS: " + checks + " gesture behavior checks");
    }
}
