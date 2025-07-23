import { ReactComponent as ChatAppCube } from '@/assets/svg/chat-app-cube.svg';
import RenameModal from '@/components/rename-modal';
import { useEnhancedDeleteDialog } from '@/hooks/use-enhanced-delete-dialog';
import {
  DeleteOutlined,
  EditOutlined,
  MessageOutlined,
  MoreOutlined,
  PlusOutlined,
  UnorderedListOutlined,
  UserOutlined,
} from '@ant-design/icons';
import {
  Avatar,
  Button,
  Card,
  Divider,
  Dropdown,
  Flex,
  MenuProps,
  Modal,
  Space,
  Spin,
  Tag,
  Tooltip,
  Typography,
} from 'antd';
import { MenuItemProps } from 'antd/lib/menu/MenuItem';
import classNames from 'classnames';
import { useCallback, useState } from 'react';
import ChatConfigurationModal from './chat-configuration-modal';
import ChatContainer from './chat-container';
import {
  useDeleteConversation,
  useEditDialog,
  useHandleItemHover,
  useRenameConversation,
  useSelectDerivedConversationList,
} from './hooks';

import EmbedModal from '@/components/api-service/embed-modal';
import { useShowEmbedModal } from '@/components/api-service/hooks';
import { useTheme } from '@/components/theme-provider';
import { SharedFrom } from '@/constants/chat';
import {
  useClickConversationCard,
  useClickDialogCard,
  useFetchNextDialog,
  useFetchNextDialogList,
  useGetChatSearchParams,
} from '@/hooks/chat-hooks';
import { useTranslate } from '@/hooks/common-hooks';
import { useSetSelectedRecord } from '@/hooks/logic-hooks';
import { IDialog } from '@/interfaces/database/chat';
import { Settings } from 'lucide-react';
import styles from './index.less';

const { Text } = Typography;

const Chat = () => {
  const { data: dialogList } = useFetchNextDialogList();
  const { data: currentDialog } = useFetchNextDialog();
  const { onRemoveConversation } = useDeleteConversation();
  const { onRemoveDialog } = useEnhancedDeleteDialog();
  const { handleClickDialog } = useClickDialogCard();
  const { handleClickConversation } = useClickConversationCard();
  const { conversationId } = useGetChatSearchParams();
  const { theme } = useTheme();
  const {
    list: conversationList,
    addTemporaryConversation,
    loading: conversationLoading,
  } = useSelectDerivedConversationList();
  const {
    activated: conversationActivated,
    handleItemEnter: handleConversationItemEnter,
    handleItemLeave: handleConversationItemLeave,
  } = useHandleItemHover();
  const {
    conversationRenameLoading,
    initialConversationName,
    onConversationRenameOk,
    conversationRenameVisible,
    hideConversationRenameModal,
    showConversationRenameModal,
  } = useRenameConversation();
  const {
    dialogSettingLoading,
    initialDialog,
    onDialogEditOk,
    dialogEditVisible,
    clearDialog,
    hideDialogEditModal,
    showDialogEditModal,
  } = useEditDialog();
  const { t } = useTranslate('chat');
  const { currentRecord } = useSetSelectedRecord<IDialog>();
  const [controller, setController] = useState(new AbortController());
  const { hideEmbedModal, embedVisible, beta } = useShowEmbedModal();

  // Permission modal state
  const [permissionModalVisible, setPermissionModalVisible] = useState(false);
  const [selectedAssistantId, setSelectedAssistantId] = useState<string>('');

  // Sidebar collapse state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleConversationCardEnter = (id: string) => () => {
    handleConversationItemEnter(id);
  };

  const handleShowChatConfigurationModal =
    (dialogId?: string): any =>
    (info: any) => {
      info?.domEvent?.preventDefault();
      info?.domEvent?.stopPropagation();
      showDialogEditModal(dialogId);
    };

  const handleShowConversationRenameModal =
    (conversationId: string): MenuItemProps['onClick'] =>
    ({ domEvent }) => {
      domEvent.preventDefault();
      domEvent.stopPropagation();
      showConversationRenameModal(conversationId);
    };

  const handleRemoveConversation =
    (conversationId: string): MenuItemProps['onClick'] =>
    ({ domEvent }) => {
      domEvent.preventDefault();
      domEvent.stopPropagation();
      onRemoveConversation([conversationId]);
    };

  const handleCreateTemporaryConversation = useCallback(() => {
    addTemporaryConversation();
  }, [addTemporaryConversation]);

  const handleShowPermissionModal = useCallback((assistantId: string) => {
    setSelectedAssistantId(assistantId);
    setPermissionModalVisible(true);
  }, []);

  const handleHidePermissionModal = useCallback(() => {
    setPermissionModalVisible(false);
    setSelectedAssistantId('');
  }, []);

  const handlePermissionSave = useCallback(() => {
    // TODO: Implement actual permission management logic here
    console.log('Saving permissions for assistant:', selectedAssistantId);
    handleHidePermissionModal();
  }, [selectedAssistantId, handleHidePermissionModal]);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev);
  }, []);

  const handleConversationCardClick = useCallback(
    (conversationId: string, isNew: boolean) => () => {
      handleClickConversation(conversationId, isNew ? 'true' : '');
      setController((pre) => {
        pre.abort();
        return new AbortController();
      });
    },
    [handleClickConversation],
  );

  const buildAssistantActionItems = (dialog: IDialog) => {
    const items: MenuProps['items'] = [
      {
        key: 'edit',
        onClick: ({ domEvent }) => {
          domEvent?.stopPropagation();
          domEvent?.preventDefault();
          showDialogEditModal(dialog.id);
        },
        label: (
          <Space>
            <EditOutlined />
            {t('edit', { keyPrefix: 'common' })}
          </Space>
        ),
      },
      {
        key: 'delete',
        onClick: ({ domEvent }) => {
          domEvent?.stopPropagation();
          domEvent?.preventDefault();
          onRemoveDialog([dialog.id]);
        },
        label: (
          <Space style={{ color: '#ff4d4f' }}>
            <DeleteOutlined />
            {t('delete', { keyPrefix: 'common' })}
          </Space>
        ),
      },
      {
        key: 'permissions',
        onClick: ({ domEvent }) => {
          domEvent?.stopPropagation();
          domEvent?.preventDefault();
          handleShowPermissionModal(dialog.id);
        },
        label: (
          <Space>
            <Settings className="size-4" />
            {t('permissionManagement', { keyPrefix: 'common' }) ||
              'Permission Management'}
          </Space>
        ),
      },
    ];

    return items;
  };

  const buildAssistantDropdownItems = () => {
    const items: MenuProps['items'] = dialogList.map((dialog) => ({
      key: dialog.id,
      onClick: () => handleClickDialog(dialog.id),
      label: (
        <Flex justify="space-between" align="center" style={{ width: 250 }}>
          <Space>
            <Avatar src={dialog.icon} shape={'square'} size="small" />
            <span>{dialog.name}</span>
          </Space>
          <Dropdown
            menu={{ items: buildAssistantActionItems(dialog) }}
            trigger={['click']}
            placement="bottomRight"
          >
            <Button
              type="text"
              size="small"
              icon={<MoreOutlined />}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
              }}
              style={{
                opacity: 0.7,
                transition: 'opacity 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '1';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '0.7';
              }}
            />
          </Dropdown>
        </Flex>
      ),
    }));

    if (items.length === 0) {
      items.push({
        key: 'empty',
        disabled: true,
        label:
          t('noAssistants', { keyPrefix: 'chat' }) || 'No assistants available',
      });
    }

    return items;
  };

  const buildConversationItems = (conversationId: string) => {
    const appItems: MenuProps['items'] = [
      {
        key: '1',
        onClick: handleShowConversationRenameModal(conversationId),
        label: (
          <Space>
            <EditOutlined />
            {t('rename', { keyPrefix: 'common' })}
          </Space>
        ),
      },
      { type: 'divider' },
      {
        key: '2',
        onClick: handleRemoveConversation(conversationId),
        label: (
          <Space>
            <DeleteOutlined />
            {t('delete', { keyPrefix: 'common' })}
          </Space>
        ),
      },
    ];

    return appItems;
  };

  return (
    <Flex className={styles.chatWrapper}>
      <div style={{ position: 'relative' }}>
        <Flex
          className={classNames(styles.singleSidebarWrapper, {
            [styles.collapsed]: sidebarCollapsed,
          })}
        >
          <div
            className={classNames(styles.sidebarContent, {
              [styles.collapsed]: sidebarCollapsed,
            })}
          >
            <Flex flex={1} vertical>
              {/* Header with Create Assistant button and dropdown */}
              <Flex
                justify="space-between"
                align="center"
                style={{ marginBottom: 16 }}
              >
                <Button
                  type="primary"
                  onClick={handleShowChatConfigurationModal()}
                  style={{ flex: 1, marginRight: 8 }}
                >
                  {t('createAssistant')}
                </Button>
                <Dropdown
                  menu={{ items: buildAssistantDropdownItems() }}
                  trigger={['click']}
                  placement="bottomRight"
                >
                  <Button
                    type="default"
                    icon={<MoreOutlined />}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  />
                </Dropdown>
              </Flex>

              {/* New Chat button */}
              <Button
                type="default"
                onClick={handleCreateTemporaryConversation}
                style={{ marginBottom: 16 }}
              >
                {t('newChat')}
              </Button>

              {/* Active Assistant Indicator */}
              {currentDialog && currentDialog.id && (
                <Card
                  size="small"
                  style={{
                    marginBottom: 16,
                    backgroundColor:
                      theme === 'dark'
                        ? 'rgba(255, 255, 255, 0.05)'
                        : 'rgba(0, 123, 255, 0.05)',
                    border: `1px solid ${theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 123, 255, 0.2)'}`,
                    borderRadius: '8px',
                  }}
                >
                  <Flex align="center" gap={12}>
                    <Avatar
                      src={currentDialog.icon}
                      shape="square"
                      size="small"
                      style={{ border: '1px solid rgba(0, 123, 255, 0.3)' }}
                    />
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          fontWeight: 'bold',
                          fontSize: '12px',
                          color:
                            theme === 'dark'
                              ? 'rgba(255, 255, 255, 0.8)'
                              : 'rgba(0, 123, 255, 0.8)',
                          marginBottom: '2px',
                        }}
                      >
                        {t('activeAssistant') || 'Active Assistant'}
                      </div>
                      <Text
                        ellipsis={{ tooltip: currentDialog.name }}
                        style={{
                          fontSize: '13px',
                          fontWeight: '500',
                          color:
                            theme === 'dark'
                              ? 'rgba(255, 255, 255, 0.9)'
                              : 'rgba(0, 0, 0, 0.8)',
                        }}
                      >
                        {currentDialog.name}
                      </Text>
                    </div>
                    <Dropdown
                      menu={{ items: buildAssistantActionItems(currentDialog) }}
                      trigger={['click']}
                      placement="bottomRight"
                    >
                      <Button
                        type="text"
                        size="small"
                        icon={<MoreOutlined />}
                        style={{
                          opacity: 0.7,
                          transition: 'opacity 0.2s',
                          color:
                            theme === 'dark'
                              ? 'rgba(255, 255, 255, 0.6)'
                              : 'rgba(0, 0, 0, 0.6)',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.opacity = '1';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.opacity = '0.7';
                        }}
                      />
                    </Dropdown>
                  </Flex>
                </Card>
              )}

              {/* Chat count display */}
              <Flex
                justify="space-between"
                align="center"
                style={{ marginBottom: 16 }}
              >
                <Space>
                  <b>{t('chat')}</b>
                  <Tag>{conversationList.length}</Tag>
                </Space>
              </Flex>

              <Divider style={{ margin: '0 0 16px 0' }} />

              {/* Conversation list */}
              <Flex vertical gap={10} className={styles.conversationContent}>
                <Spin
                  spinning={conversationLoading}
                  wrapperClassName={styles.chatSpin}
                >
                  {conversationList.map((x) => (
                    <Card
                      key={x.id}
                      hoverable
                      onClick={handleConversationCardClick(x.id, x.is_new)}
                      onMouseEnter={handleConversationCardEnter(x.id)}
                      onMouseLeave={handleConversationItemLeave}
                      className={classNames(styles.conversationCard, {
                        [theme === 'dark'
                          ? styles.conversationCardSelectedDark
                          : styles.conversationCardSelected]:
                          x.id === conversationId,
                      })}
                    >
                      <Flex justify="space-between" align="center">
                        <div>
                          <Text
                            ellipsis={{ tooltip: x.name }}
                            style={{ width: 180 }}
                          >
                            {x.name}
                          </Text>
                        </div>
                        {conversationActivated === x.id &&
                          x.id !== '' &&
                          !x.is_new && (
                            <section>
                              <Dropdown
                                menu={{ items: buildConversationItems(x.id) }}
                              >
                                <ChatAppCube
                                  className={styles.cubeIcon}
                                ></ChatAppCube>
                              </Dropdown>
                            </section>
                          )}
                      </Flex>
                    </Card>
                  ))}
                </Spin>
              </Flex>
            </Flex>
          </div>

          {/* Collapsed Sidebar Content - Minimal Icons */}
          <div className={styles.collapsedSidebarContent}>
            {/* Create Assistant Button */}
            <Tooltip title={t('createAssistant')} placement="right">
              <Button
                className={styles.miniButton}
                onClick={handleShowChatConfigurationModal()}
                type="text"
              >
                <PlusOutlined className={styles.miniIcon} />
              </Button>
            </Tooltip>

            {/* New Chat Button */}
            <Tooltip title={t('newChat')} placement="right">
              <Button
                className={styles.miniButton}
                onClick={handleCreateTemporaryConversation}
                type="text"
              >
                <MessageOutlined className={styles.miniIcon} />
              </Button>
            </Tooltip>

            {/* Active Assistant Display */}
            {currentDialog && currentDialog.id && (
              <Tooltip
                title={`${t('activeAssistant')}: ${currentDialog.name}`}
                placement="right"
              >
                <div className={styles.activeAssistantMini}>
                  {currentDialog.icon ? (
                    <Avatar
                      src={currentDialog.icon}
                      shape="square"
                      size={36}
                      style={{ borderRadius: '8px' }}
                    />
                  ) : (
                    <UserOutlined className={styles.miniIcon} />
                  )}
                </div>
              </Tooltip>
            )}

            {/* Chat List Indicator */}
            <Tooltip
              title={`${t('chat')}: ${conversationList.length} ${conversationList.length === 1 ? 'conversation' : 'conversations'}`}
              placement="right"
            >
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '8px',
                }}
              >
                <Button className={styles.miniButton} type="text" disabled>
                  <UnorderedListOutlined className={styles.miniIcon} />
                </Button>
                <div
                  className={`${styles.chatListIndicator} ${conversationList.length > 0 ? styles.hasChats : ''}`}
                />
              </div>
            </Tooltip>
          </div>
        </Flex>
        {/* Sidebar Toggle Button */}
        <Button
          className={styles.sidebarToggleButton}
          onClick={toggleSidebar}
          type="text"
          size="small"
        >
          <span
            className={classNames(styles.toggleIcon, {
              [styles.collapsed]: sidebarCollapsed,
            })}
          >
            {sidebarCollapsed ? '→' : '←'}
          </span>
        </Button>
      </div>
      <Divider
        type={'vertical'}
        className={classNames(styles.divider, {
          [styles.collapsed]: sidebarCollapsed,
        })}
      ></Divider>
      <ChatContainer controller={controller}></ChatContainer>
      {dialogEditVisible && (
        <ChatConfigurationModal
          visible={dialogEditVisible}
          initialDialog={initialDialog}
          showModal={showDialogEditModal}
          hideModal={hideDialogEditModal}
          loading={dialogSettingLoading}
          onOk={onDialogEditOk}
          clearDialog={clearDialog}
        ></ChatConfigurationModal>
      )}
      <RenameModal
        visible={conversationRenameVisible}
        hideModal={hideConversationRenameModal}
        onOk={onConversationRenameOk}
        initialName={initialConversationName}
        loading={conversationRenameLoading}
      ></RenameModal>

      {embedVisible && (
        <EmbedModal
          visible={embedVisible}
          hideModal={hideEmbedModal}
          token={currentRecord.id}
          form={SharedFrom.Chat}
          beta={beta}
          isAgent={false}
        ></EmbedModal>
      )}

      {/* Permission Management Modal */}
      <Modal
        title="Permission Management"
        open={permissionModalVisible}
        onOk={handlePermissionSave}
        onCancel={handleHidePermissionModal}
        okText="Save"
        cancelText="Cancel"
        width={600}
      >
        <div style={{ padding: '20px 0' }}>
          <p style={{ marginBottom: '16px', fontSize: '14px', color: '#666' }}>
            Manage permissions for Assistant ID:{' '}
            <strong>{selectedAssistantId}</strong>
          </p>

          <div
            style={{
              padding: '20px',
              backgroundColor: '#f5f5f5',
              borderRadius: '8px',
              textAlign: 'center',
            }}
          >
            <p style={{ margin: 0, fontSize: '14px', color: '#888' }}>
              Permission management functionality will be implemented here.
            </p>
            <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#aaa' }}>
              This includes user access control, role assignments, and sharing
              settings.
            </p>
          </div>
        </div>
      </Modal>
    </Flex>
  );
};

export default Chat;
