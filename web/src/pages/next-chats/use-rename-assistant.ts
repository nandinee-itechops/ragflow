import { useSetNextDialog } from '@/hooks/chat-hooks';
import { useSetModalState } from '@/hooks/common-hooks';
import { IDialog } from '@/interfaces/database/chat';
import { useCallback, useState } from 'react';

export const useRenameAssistant = () => {
  const [assistant, setAssistant] = useState<IDialog>({} as IDialog);
  const {
    visible: assistantRenameVisible,
    hideModal: hideAssistantRenameModal,
    showModal: showAssistantRenameModal,
  } = useSetModalState();
  const { setDialog, loading } = useSetNextDialog();

  const onAssistantRenameOk = useCallback(
    async (name: string) => {
      const ret = await setDialog({
        ...assistant,
        name,
      });

      if (ret === 0) {
        hideAssistantRenameModal();
      }
    },
    [setDialog, assistant, hideAssistantRenameModal],
  );

  const handleShowAssistantRenameModal = useCallback(
    async (record: IDialog) => {
      setAssistant(record);
      showAssistantRenameModal();
    },
    [showAssistantRenameModal],
  );

  return {
    assistantRenameLoading: loading,
    initialAssistantName: assistant?.name,
    onAssistantRenameOk,
    assistantRenameVisible,
    hideAssistantRenameModal,
    showAssistantRenameModal: handleShowAssistantRenameModal,
  };
};
