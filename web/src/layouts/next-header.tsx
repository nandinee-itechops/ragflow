import { RAGFlowAvatar } from '@/components/ragflow-avatar';
import { useTheme } from '@/components/theme-provider';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { LanguageList, LanguageMap } from '@/constants/common';
import { useChangeLanguage } from '@/hooks/logic-hooks';
import { useNavigatePage } from '@/hooks/logic-hooks/navigate-hooks';
import { useNavigateWithFromState } from '@/hooks/route-hook';
import { useFetchUserInfo } from '@/hooks/user-setting-hooks';
import { Routes } from '@/routes';
import { camelCase } from 'lodash';
import {
  ChevronDown,
  CircleHelp,
  Cpu,
  File,
  Github,
  Library,
  MessageSquareText,
  Moon,
  MoreHorizontal,
  Search,
  Sun,
} from 'lucide-react';
import React, { useCallback, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'umi';

const handleDocHelpCLick = () => {
  window.open('https://ragflow.io/docs/dev/category/guides', 'target');
};

export function Header() {
  const { t } = useTranslation();
  const { pathname } = useLocation();
  const navigate = useNavigateWithFromState();
  const { navigateToProfile } = useNavigatePage();

  const changeLanguage = useChangeLanguage();
  const { setTheme, theme } = useTheme();

  const {
    data: { language = 'English', avatar, nickname },
  } = useFetchUserInfo();

  const handleItemClick = (key: string) => () => {
    changeLanguage(key);
  };

  const items = LanguageList.map((x) => ({
    key: x,
    label: <span>{LanguageMap[x as keyof typeof LanguageMap]}</span>,
  }));

  const onThemeClick = React.useCallback(() => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  }, [setTheme, theme]);

  const tagsData = useMemo(
    () => [
      { path: Routes.Datasets, name: t('header.knowledgeBase'), icon: Library },
      { path: Routes.Chats, name: t('header.chat'), icon: MessageSquareText },
      { path: Routes.Searches, name: t('header.search'), icon: Search },
      { path: Routes.Agents, name: t('header.flow'), icon: Cpu },
      { path: Routes.Files, name: t('header.fileManager'), icon: File },
    ],
    [t],
  );

  const navigationOptions = useMemo(() => {
    return tagsData.map((tag) => {
      const HeaderIcon = tag.icon;
      return {
        name: tag.name,
        path: tag.path,
        icon: HeaderIcon,
      };
    });
  }, [tagsData]);

  const currentPath = useMemo(() => {
    return (
      tagsData.find((x) => pathname.startsWith(x.path))?.path || Routes.Datasets
    );
  }, [pathname, tagsData]);

  const handleNavigationClick = useCallback(
    (path: Routes) => {
      navigate(path);
    },
    [navigate],
  );

  const handleLogoClick = useCallback(() => {
    navigate(Routes.Datasets); // Navigate to Knowledge Base instead of Home
  }, [navigate]);

  // Keyboard shortcut for menu (Alt + M)
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.altKey && event.key === 'm') {
        event.preventDefault();
        // Focus the menu trigger
        const menuTrigger = document.querySelector(
          '[data-menu-trigger]',
        ) as HTMLElement;
        if (menuTrigger) {
          menuTrigger.click();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <section className="px-6 py-4 flex justify-between items-center border-b border-gray-200 bg-gradient-to-r from-white to-gray-50 shadow-sm">
      <div className="flex items-center gap-4">
        <img
          src={'/Itechops_logo.png'}
          alt="RAGFlow Logo"
          className="h-12 w-auto cursor-pointer hover:opacity-80 transition-all duration-200 hover:scale-105"
          onClick={handleLogoClick}
        />
        <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-gray-200 shadow-sm">
          <Github className="size-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-700">21.5k stars</span>
        </div>
      </div>

      {/* Navigation Menu - Centered Three-Dots Menu */}
      <div className="flex-1 flex justify-center">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              data-menu-trigger
              variant="outline"
              className="flex items-center gap-2 px-4 py-2.5 hover:bg-blue-50 hover:border-blue-300 rounded-lg transition-all duration-200 shadow-sm border-gray-300"
              title="Navigation Menu (Alt + M)"
            >
              <MoreHorizontal className="size-5" />
              <span className="text-sm font-medium">Menu</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            align="center"
            className="w-72 p-3 shadow-xl border border-gray-200 bg-white rounded-lg"
          >
            <div className="px-3 py-2 text-xs font-bold text-gray-600 uppercase tracking-wider border-b border-gray-100 mb-2">
              🚀 Navigation
            </div>
            {navigationOptions.map((option) => {
              const Icon = option.icon;
              const isActive = currentPath === option.path;
              return (
                <DropdownMenuItem
                  key={option.path}
                  onClick={() => handleNavigationClick(option.path)}
                  className={`flex items-center gap-4 px-4 py-3 cursor-pointer rounded-lg transition-all duration-200 mb-1 ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 font-semibold border border-blue-200 shadow-sm'
                      : 'hover:bg-gray-50 text-gray-700 hover:text-gray-900 hover:shadow-sm'
                  }`}
                >
                  <div
                    className={`p-2 rounded-md ${isActive ? 'bg-blue-500' : 'bg-gray-100'}`}
                  >
                    <Icon
                      className={`size-4 ${isActive ? 'text-white' : 'text-gray-600'}`}
                    />
                  </div>
                  <span className="text-sm font-medium flex-1">
                    {option.name}
                  </span>
                  {isActive && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                  )}
                </DropdownMenuItem>
              );
            })}
            <div className="mt-3 pt-2 border-t border-gray-100">
              <div className="text-xs text-gray-500 text-center">
                Choose your workspace
              </div>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="flex items-center gap-4 text-text-badge">
        <DropdownMenu>
          <DropdownMenuTrigger>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors cursor-pointer">
              <span className="text-sm font-medium">
                {t(`common.${camelCase(language)}`)}
              </span>
              <ChevronDown className="size-4" />
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {items.map((x) => (
              <DropdownMenuItem key={x.key} onClick={handleItemClick(x.key)}>
                {x.label}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        <Button
          variant={'ghost'}
          onClick={handleDocHelpCLick}
          className="hover:bg-gray-100"
        >
          <CircleHelp className="size-5" />
        </Button>
        <Button
          variant={'ghost'}
          onClick={onThemeClick}
          className="hover:bg-gray-100"
        >
          {theme === 'light' ? (
            <Sun className="size-5" />
          ) : (
            <Moon className="size-5" />
          )}
        </Button>
        <div className="relative">
          <RAGFlowAvatar
            name={nickname}
            avatar={avatar}
            className="size-9 cursor-pointer hover:ring-2 hover:ring-blue-300 transition-all duration-200"
            onClick={navigateToProfile}
          ></RAGFlowAvatar>
          <Badge className="h-5 w-8 absolute font-bold p-0 justify-center -right-3 -top-1 text-white bg-gradient-to-r from-blue-500 to-purple-600 shadow-lg">
            Pro
          </Badge>
        </div>
      </div>
    </section>
  );
}
