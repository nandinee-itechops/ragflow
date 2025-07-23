import { useCallback } from 'react';
import { useSearchParams } from 'umi';
import { useGetChatSearchParams, useRemoveNextDialog } from './chat-hooks';
import { useShowDeleteConfirm } from './common-hooks';

/**
 * Enhanced delete dialog hook that handles clearing active assistant state
 * when the currently active assistant is deleted
 */
export const useEnhancedDeleteDialog = () => {
  const showDeleteConfirm = useShowDeleteConfirm();
  const { removeDialog } = useRemoveNextDialog();
  const { dialogId } = useGetChatSearchParams();
  const [, setSearchParams] = useSearchParams();

  const onRemoveDialogEnhanced = useCallback(
    (dialogIds: Array<string>) => {
      // Check if any of the assistants being deleted is the currently active one
      const isCurrentAssistantBeingDeleted = dialogIds.includes(dialogId);

      showDeleteConfirm({
        onOk: () => {
          // Delete the assistant(s)
          removeDialog(dialogIds);

          // If the active assistant was deleted, clear the dialogId from URL params
          // This will automatically clear the current dialog state and related data
          if (isCurrentAssistantBeingDeleted && dialogId) {
            const currentParams = new URLSearchParams(window.location.search);
            currentParams.delete('dialogId');
            currentParams.delete('conversationId'); // Also clear conversation if any
            setSearchParams(currentParams);
          }
        },
      });
    },
    [showDeleteConfirm, removeDialog, dialogId, setSearchParams],
  );

  return { onRemoveDialog: onRemoveDialogEnhanced };
};
