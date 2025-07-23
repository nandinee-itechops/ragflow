import { ConfirmDeleteDialog } from '@/components/confirm-delete-dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useEnhancedDeleteDialog } from '@/hooks/use-enhanced-delete-dialog';
import { IDialog } from '@/interfaces/database/chat';
import { PenLine, Settings, Trash2 } from 'lucide-react';
import { MouseEventHandler, PropsWithChildren, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

export interface IUseRenameAssistant {
  showAssistantRenameModal: (assistant: IDialog) => void;
}

export function AssistantDropdown({
  children,
  showAssistantRenameModal,
  showAssistantEditModal,
  showPermissionManagementModal,
  assistant,
}: PropsWithChildren &
  Pick<IUseRenameAssistant, 'showAssistantRenameModal'> & {
    assistant: IDialog;
    showAssistantEditModal?: (assistant: IDialog) => void;
    showPermissionManagementModal?: (assistant: IDialog) => void;
  }) {
  const { t } = useTranslation();
  const { onRemoveDialog } = useEnhancedDeleteDialog();

  const handleShowEditModal: MouseEventHandler<HTMLDivElement> = useCallback(
    (e) => {
      e.stopPropagation();
      showAssistantEditModal?.(assistant);
    },
    [assistant, showAssistantEditModal],
  );

  const handleShowPermissionManagement: MouseEventHandler<HTMLDivElement> =
    useCallback(
      (e) => {
        e.stopPropagation();
        showPermissionManagementModal?.(assistant);
      },
      [assistant, showPermissionManagementModal],
    );

  const handleDelete: MouseEventHandler<HTMLDivElement> = useCallback(() => {
    onRemoveDialog([assistant.id]);
  }, [assistant.id, onRemoveDialog]);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>{children}</DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={handleShowEditModal}>
          {t('common.edit')} <PenLine />
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleShowPermissionManagement}>
          {t('permissionManagement')} <Settings />
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <ConfirmDeleteDialog onOk={handleDelete}>
          <DropdownMenuItem
            className="text-text-delete-red"
            onSelect={(e) => {
              e.preventDefault();
            }}
            onClick={(e) => {
              e.stopPropagation();
            }}
          >
            {t('common.delete')} <Trash2 />
          </DropdownMenuItem>
        </ConfirmDeleteDialog>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
