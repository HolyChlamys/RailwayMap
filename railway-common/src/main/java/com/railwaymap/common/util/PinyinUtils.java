package com.railwaymap.common.util;

import net.sourceforge.pinyin4j.PinyinHelper;
import net.sourceforge.pinyin4j.format.HanyuPinyinCaseType;
import net.sourceforge.pinyin4j.format.HanyuPinyinOutputFormat;
import net.sourceforge.pinyin4j.format.HanyuPinyinToneType;
import net.sourceforge.pinyin4j.format.HanyuPinyinVCharType;
import net.sourceforge.pinyin4j.format.exception.BadHanyuPinyinOutputFormatCombination;

/**
 * 中文→拼音/首字母 转换工具
 */
public final class PinyinUtils {

    private static final HanyuPinyinOutputFormat FORMAT = new HanyuPinyinOutputFormat();

    static {
        FORMAT.setCaseType(HanyuPinyinCaseType.LOWERCASE);
        FORMAT.setToneType(HanyuPinyinToneType.WITHOUT_TONE);
        FORMAT.setVCharType(HanyuPinyinVCharType.WITH_V);
    }

    private PinyinUtils() {}

    /**
     * 获取中文全拼 (小写空格分隔)
     * "北京南" → "bei jing nan"
     */
    public static String toPinyin(String chinese) {
        if (chinese == null || chinese.isEmpty()) {
            return chinese;
        }
        StringBuilder sb = new StringBuilder();
        for (char c : chinese.toCharArray()) {
            try {
                String[] arr = PinyinHelper.toHanyuPinyinStringArray(c, FORMAT);
                if (arr != null && arr.length > 0) {
                    if (!sb.isEmpty()) sb.append(' ');
                    sb.append(arr[0]);
                }
            } catch (BadHanyuPinyinOutputFormatCombination ignored) {
            }
        }
        return sb.toString();
    }

    /**
     * 获取中文首字母 (小写无空格)
     * "北京南" → "bjn"
     */
    public static String toFirstLetters(String chinese) {
        if (chinese == null || chinese.isEmpty()) {
            return chinese;
        }
        StringBuilder sb = new StringBuilder();
        for (char c : chinese.toCharArray()) {
            try {
                String[] arr = PinyinHelper.toHanyuPinyinStringArray(c, FORMAT);
                if (arr != null && arr.length > 0) {
                    sb.append(arr[0].charAt(0));
                }
            } catch (BadHanyuPinyinOutputFormatCombination ignored) {
            }
        }
        return sb.toString();
    }

    /**
     * 获取中文全拼 (无空格)
     * "北京南" → "beijingnan"
     */
    public static String toPinyinNoSpace(String chinese) {
        return toPinyin(chinese).replace(" ", "");
    }
}
