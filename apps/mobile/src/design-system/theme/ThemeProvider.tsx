import React, { createContext, useContext, useMemo } from 'react';
import { useColorScheme } from 'react-native';
import { makeTheme, Theme } from './theme';

const ThemeContext = createContext<Theme>(makeTheme(false));

/**
 * Drives light/dark from the OS appearance. `forceScheme` overrides it
 * (used by the gallery previews and screenshot audits).
 */
export function ThemeProvider({
  children,
  forceScheme,
}: {
  children: React.ReactNode;
  forceScheme?: 'light' | 'dark';
}) {
  const system = useColorScheme();
  const isDark = forceScheme ? forceScheme === 'dark' : system === 'dark';
  const theme = useMemo(() => makeTheme(isDark), [isDark]);
  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
}

export const useTheme = (): Theme => useContext(ThemeContext);
