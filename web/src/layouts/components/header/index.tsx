import { ReactComponent as FileIcon } from '@/assets/svg/file-management.svg';
import { ReactComponent as GraphIcon } from '@/assets/svg/graph.svg';
import { ReactComponent as KnowledgeBaseIcon } from '@/assets/svg/knowledge-base.svg';
import { useTranslate } from '@/hooks/common-hooks';
import { useFetchAppConf } from '@/hooks/logic-hooks';
import { useNavigateWithFromState } from '@/hooks/route-hook';
import {
  MessageOutlined,
  MoreOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { Button, Flex, Layout, Space, theme } from 'antd';
import { useCallback, useMemo } from 'react';
import { useLocation } from 'umi';
import Toolbar from '../right-toolbar';

import { useTheme } from '@/components/theme-provider';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import styles from './index.less';

const { Header } = Layout;

const RagHeader = () => {
  const {
    token: { colorBgContainer },
  } = theme.useToken();
  const navigate = useNavigateWithFromState();
  const { pathname } = useLocation();
  const { t } = useTranslate('header');
  const appConf = useFetchAppConf();
  const { theme: themeRag } = useTheme();
  const tagsData = useMemo(
    () => [
      { path: '/knowledge', name: t('knowledgeBase'), icon: KnowledgeBaseIcon },
      { path: '/chat', name: t('chat'), icon: MessageOutlined },
      { path: '/search', name: t('search'), icon: SearchOutlined },
      { path: '/flow', name: t('flow'), icon: GraphIcon },
      { path: '/file', name: t('fileManager'), icon: FileIcon },
    ],
    [t],
  );

  const handleMenuItemClick = useCallback(
    (path: string) => {
      navigate(path);
    },
    [navigate],
  );

  const handleLogoClick = useCallback(() => {
    navigate('/');
  }, [navigate]);

  return (
    <Header
      style={{
        padding: '0 16px',
        background: colorBgContainer,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        height: '72px',
      }}
    >
      <Space size={12} align="center">
        <a href={window.location.origin}>
          <Space
            size={12}
            onClick={handleLogoClick}
            className={styles.logoWrapper}
          >
            <img src="/Itechops_logo.png" alt="" className={styles.appIcon} />
            <span className={styles.appName}>{appConf.appName}</span>
          </Space>
        </a>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="text"
              icon={<MoreOutlined />}
              className={styles.menuTrigger}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '40px',
                height: '40px',
                borderRadius: '6px',
                border: `1px solid ${themeRag === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'}`,
                backgroundColor:
                  themeRag === 'dark'
                    ? 'rgba(255, 255, 255, 0.05)'
                    : 'rgba(0, 0, 0, 0.02)',
              }}
            />
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="start">
            {tagsData.map((item) => {
              const IconComponent = item.icon;
              const isActive = pathname.startsWith(item.path);
              return (
                <DropdownMenuItem
                  key={item.name}
                  onClick={() => handleMenuItemClick(item.path)}
                  className={`cursor-pointer ${isActive ? 'bg-accent text-accent-foreground' : ''}`}
                >
                  <Flex align="center" gap={8}>
                    <IconComponent
                      className={styles.radioButtonIcon}
                      style={{
                        color: isActive
                          ? 'var(--colors-text-core-standard)'
                          : 'var(--colors-text-neutral-standard)',
                        width: '16px',
                        height: '16px',
                      }}
                    />
                    <span>{item.name}</span>
                  </Flex>
                </DropdownMenuItem>
              );
            })}
          </DropdownMenuContent>
        </DropdownMenu>
      </Space>
      <Toolbar></Toolbar>
    </Header>
  );
};

export default RagHeader;
