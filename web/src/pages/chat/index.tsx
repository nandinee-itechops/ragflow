import { ReactComponent as ChatAppCube } from '@/assets/svg/chat-app-cube.svg';
import RenameModal from '@/components/rename-modal';
import { DeleteOutlined, EditOutlined, MoreOutlined } from '@ant-design/icons';
import {
  Avatar,
  Button,
  Card,
  Divider,
  Dropdown,
  Flex,
  MenuProps,
  Space,
  Spin,
  Tag,
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
import styles from './index.less';

const { Text } = Typography;

const Chat = () => {
  const { data: dialogList } = useFetchNextDialogList();
  const { data: currentDialog } = useFetchNextDialog();
  const { onRemoveConversation } = useDeleteConversation();
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

  const buildAssistantDropdownItems = () => {
    const items: MenuProps['items'] = dialogList.map((dialog) => ({
      key: dialog.id,
      onClick: () => handleClickDialog(dialog.id),
      label: (
        <Space>
          <Avatar src={dialog.icon} shape={'square'} size="small" />
          <span>{dialog.name}</span>
        </Space>
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
      <Flex className={styles.singleSidebarWrapper}>
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
      </Flex>
      <Divider type={'vertical'} className={styles.divider}></Divider>
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
    </Flex>
  );
};

export default Chat;
