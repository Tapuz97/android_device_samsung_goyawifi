"""Apply the source changes for the next grouped Android build."""
from pathlib import Path
import difflib
import subprocess
import sys

project = Path(__file__).resolve().parents[1]
tree = Path(sys.argv[1])


def apply(repo, patch_name, edits):
    patch = project / "patches" / patch_name
    if not patch.exists():
        chunks = []
        for relative, replacements in edits.items():
            old = (tree / repo / relative).read_text()
            new = old
            for before, after in replacements:
                assert new.count(before) == 1, (relative, before)
                new = new.replace(before, after)
            chunks.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                               "a/" + relative, "b/" + relative))
        patch.write_text("".join(chunks), encoding="utf-8")
    args = ["git", "-C", str(tree / repo), "apply"]
    if subprocess.run(args + ["--reverse", "--check", str(patch)], capture_output=True).returncode:
        subprocess.run(args + ["--check", str(patch)], check=True)
        subprocess.run(args + [str(patch)], check=True)


apply("build/soong", "0086-soong-preopt-selected-t110-tethering-app.patch", {
    "java/dexpreopt.go": [
        (
            'func (d *dexpreopter) preoptFlattenedApexApp(ctx android.BaseModuleContext) bool {\n'
            '\tif !ctx.Config().FlattenApex() || !ctx.Config().VendorConfig("t110").Bool("preopt_flattened_apex_apps") || !isApexVariant(ctx) {\n'
            '\t\treturn false\n\t}\n'
            '\tif _, ok := ctx.Module().(*AndroidApp); !ok {\n\t\treturn false\n\t}\n'
            '\tselected := ctx.Config().VendorConfig("t110").String("preopt_apex_name")\n'
            '\tinfo := ctx.Provider(android.ApexInfoProvider).(android.ApexInfo)\n'
            '\treturn selected != "" && inList(selected, info.InApexVariants) && inList(moduleName(ctx), dexpreopt.GetGlobalConfig(ctx).SpeedApps)\n}',
            'func (d *dexpreopter) preoptFlattenedApexApp(ctx android.BaseModuleContext) bool {\n'
            '\treturn d.flattenedApexAppName(ctx) != ""\n}\n\n'
            'func (d *dexpreopter) flattenedApexAppName(ctx android.BaseModuleContext) string {\n'
            '\tif !ctx.Config().FlattenApex() || !ctx.Config().VendorConfig("t110").Bool("preopt_flattened_apex_apps") || !isApexVariant(ctx) {\n'
            '\t\treturn ""\n\t}\n'
            '\tif _, ok := ctx.Module().(*AndroidApp); !ok || !inList(moduleName(ctx), dexpreopt.GetGlobalConfig(ctx).SpeedApps) {\n'
            '\t\treturn ""\n\t}\n'
            '\tinfo := ctx.Provider(android.ApexInfoProvider).(android.ApexInfo)\n'
            '\tfor _, name := range strings.Fields(ctx.Config().VendorConfig("t110").String("preopt_apex_name")) {\n'
            '\t\tif inList(name, info.InApexVariants) {\n\t\t\treturn name\n\t\t}\n\t}\n'
            '\treturn ""\n}'
        ),
        ('\tif d.preoptFlattenedApexApp(ctx) {\n'
         '\t\tselected := ctx.Config().VendorConfig("t110").String("preopt_apex_name")\n',
         '\tif selected := d.flattenedApexAppName(ctx); selected != "" {\n'),
    ],
})

apply("frameworks/base", "0087-policy-honor-advanced-restart-in-fallback-menu.patch", {
    "services/core/java/com/android/server/policy/LegacyGlobalActions.java": [
        ("import java.util.ArrayList;\n", "import org.lineageos.internal.util.PowerMenuUtils;\n\nimport java.util.ArrayList;\n"),
        ("                mItems.add(new RestartAction(mContext, mWindowManagerFuncs));\n",
         "                mItems.add(new RestartAction(mContext, mWindowManagerFuncs));\n"
         "                if (canShowAdvancedRestart()) {\n"
         "                    mItems.add(new RestartToAction(R.string.global_action_restart_to_recovery,\n"
         "                            \"recovery\"));\n"
         "                    mItems.add(new RestartToAction(R.string.global_action_restart_to_bootloader,\n"
         "                            \"bootloader\"));\n"
         "                }\n"),
        ("    private class BugReportAction extends SinglePressAction implements LongPressAction {\n",
         "    private boolean canShowAdvancedRestart() {\n"
         "        return ActivityManager.getCurrentUser() == UserHandle.USER_SYSTEM\n"
         "                && PowerMenuUtils.isAdvancedRestartPossible(mContext);\n"
         "    }\n\n"
         "    private final class RestartToAction extends SinglePressAction {\n"
         "        private final String mReason;\n\n"
         "        RestartToAction(int label, String reason) {\n"
         "            super(R.drawable.ic_restart, label);\n"
         "            mReason = reason;\n"
         "        }\n\n"
         "        @Override\n"
         "        public void onPress() {\n"
         "            if (canShowAdvancedRestart()) {\n"
         "                mWindowManagerFuncs.reboot(true /* confirm */, mReason);\n"
         "            }\n"
         "        }\n\n"
         "        @Override\n"
         "        public boolean showDuringKeyguard() {\n"
         "            return true;\n"
         "        }\n\n"
         "        @Override\n"
         "        public boolean showBeforeProvisioning() {\n"
         "            return true;\n"
         "        }\n"
         "    }\n\n"
         "    private class BugReportAction extends SinglePressAction implements LongPressAction {\n"),
    ],
    "core/res/res/values/strings.xml": [
        ('    <string name="global_action_restart">Restart</string>\n',
         '    <string name="global_action_restart">Restart</string>\n'
         '    <!-- Power menu action to restart into device recovery. -->\n'
         '    <string name="global_action_restart_to_recovery">Restart to recovery</string>\n'
         '    <!-- Power menu action to restart into the bootloader. -->\n'
         '    <string name="global_action_restart_to_bootloader">Restart to bootloader</string>\n'),
    ],
})

apply("frameworks/base", "0088-framework-export-fallback-restart-labels.patch", {
    "core/res/res/values/symbols.xml": [
        ('  <java-symbol type="string" name="global_action_restart" />\n',
         '  <java-symbol type="string" name="global_action_restart" />\n'
         '  <java-symbol type="string" name="global_action_restart_to_recovery" />\n'
         '  <java-symbol type="string" name="global_action_restart_to_bootloader" />\n'),
    ],
})

# This Samsung board selects recovery through PMIC registers, not a BCB in misc.
# Keep Android's normal BCB behavior unless the board explicitly opts in.
apply("system/core", "0091-init-allow-pmic-recovery-without-misc.patch", {
    "init/reboot.cpp": [
        ('            } else if (reboot_target == "recovery") {\n',
         '            } else if (reboot_target == "recovery" &&\n'
         '                       !GetBoolProperty("ro.t110.reboot_without_misc", false)) {\n'),
    ],
})

# Linux 3.4 reports the original eight address flags in ifaddrmsg. The newer
# IFA_FLAGS attribute is optional; validate it strictly when it is supplied.
apply("frameworks/libs/net", "0092-netlink-accept-legacy-address-header-flags.patch", {
    "common/device/com/android/net/module/util/netlink/RtNetlinkAddressMessage.java": [
        ('        // IFA_FLAGS. All the flags are in the IF_FLAGS attribute. This should always be present,\n'
         '        // and will overwrite the flags set above.\n',
         '        // Newer kernels provide all flags in IFA_FLAGS. Older kernels only\n'
         '        // supply the eight flags above in ifaddrmsg.\n'),
        ('        if (nlAttr == null) return null;\n'
         '        final Integer value = nlAttr.getValueAsInteger();\n'
         '        if (value == null) return null;\n'
         '        addrMsg.mFlags = value;\n',
         '        if (nlAttr != null) {\n'
         '            final Integer value = nlAttr.getValueAsInteger();\n'
         '            if (value == null) return null;\n'
         '            addrMsg.mFlags = value;\n'
         '        }\n'),
    ],
})

# Both operands are literal strings. Keep all palette values and theme behavior
# while removing repeated ICU regex compilation during SystemUI startup.
apply("frameworks/base", "0093-tonal-parse-palettes-with-literal-replacement.patch", {
    "core/java/com/android/internal/colorextraction/types/Tonal.java": [
        ('            String[] tokens = attributeValue.replaceAll(" ", "").replaceAll("\\n", "").split(",");\n',
         '            String[] tokens = attributeValue.replace(" ", "").replace("\\n", "").split(",");\n'),
    ],
})

apply("frameworks/libs/net", "0094-tests-legacy-netlink-address-flags.patch", {
    "common/tests/unit/src/com/android/net/module/util/netlink/RtNetlinkAddressMessageTest.java": [
        ('    private static final String RTM_NEWADDR_PACK_HEX =\n',
         '''    @Test
    public void testLegacyIpv4AddressWithoutFlagsAttribute() {
        // Captured Linux 3.4 RTM_NEWADDR layout with anonymized addresses.
        final ByteBuffer buffer = toByteBuffer(
                "3C0000001400000000000000F7EFFFFF0218800004000000"
                + "08000100C000026C08000200C000026C08000400C00002FF"
                + "0A000300776C616E30000000");
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        final RtNetlinkAddressMessage msg =
                (RtNetlinkAddressMessage) NetlinkMessage.parse(buffer, NETLINK_ROUTE);
        assertNotNull(msg);
        assertEquals(InetAddresses.parseNumericAddress("192.0.2.108"), msg.getIpAddress());
        assertEquals(24, msg.getIfaddrHeader().prefixLen);
        assertEquals(4, msg.getIfaddrHeader().index);
        assertEquals(0x80, msg.getFlags());
        assertNull(msg.getIfacacheInfo());
    }

    @Test
    public void testLegacyIpv6AddressWithoutFlagsAttribute() {
        final ByteBuffer buffer = toByteBuffer(
                "400000001400000000000000000000000A4080FD04000000"
                + "14000100FE8000000000000002005EFFFE100001"
                + "14000600FFFFFFFFFFFFFFFF43EF070043EF0700");
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        final RtNetlinkAddressMessage msg =
                (RtNetlinkAddressMessage) NetlinkMessage.parse(buffer, NETLINK_ROUTE);
        assertNotNull(msg);
        assertEquals(InetAddresses.parseNumericAddress("fe80::200:5eff:fe10:1"),
                msg.getIpAddress());
        assertEquals(0x80, msg.getFlags());
        assertNotNull(msg.getIfacacheInfo());
    }

    @Test
    public void testExtendedAddressFlagsOverrideHeader() {
        final ByteBuffer buffer = toByteBuffer(RTM_NEWADDR_HEX.substring(0,
                RTM_NEWADDR_HEX.length() - 8) + "80010000");
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        final RtNetlinkAddressMessage msg =
                (RtNetlinkAddressMessage) NetlinkMessage.parse(buffer, NETLINK_ROUTE);
        assertNotNull(msg);
        assertEquals(0x180, msg.getFlags());
    }

    @Test
    public void testMalformedPresentFlagsAttributeRejected() {
        final ByteBuffer buffer = toByteBuffer(RTM_NEWADDR_HEX.substring(0,
                RTM_NEWADDR_HEX.length() - 16) + "0600080080000000");
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        assertNull(NetlinkMessage.parse(buffer, NETLINK_ROUTE));
    }

    private static final String RTM_NEWADDR_PACK_HEX =
'''),
    ],
})
