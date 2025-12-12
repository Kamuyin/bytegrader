import React, { useState, useEffect } from 'react';
import {
  Dialog,
  Button,
  FlexBox,
  FlexBoxJustifyContent,
  FlexBoxAlignItems,
  Text,
  Icon,
  Input,
  CheckBox
} from '@ui5/webcomponents-react';
import { ContentsManager } from '@jupyterlab/services';
import { Contents } from '@jupyterlab/services';
import '@ui5/webcomponents-icons/dist/folder.js';
import '@ui5/webcomponents-icons/dist/document.js';
import '@ui5/webcomponents-icons/dist/navigation-up-arrow.js';
import '@ui5/webcomponents-icons/dist/home.js';

interface FileItem {
  id: string;
  name: string;
  type: 'file' | 'directory';
  path: string;
  isNotebook?: boolean;
  size?: number;
  lastModified?: Date;
}

interface FilePickerProps {
  open: boolean;
  onClose: () => void;
  onFilesSelected?: (files: FileItem[]) => void;
  multiSelect?: boolean;
  fileTypes?: string[];
  title?: string;
}

const FilePickerDialog: React.FC<FilePickerProps> = ({
  open,
  onClose,
  onFilesSelected,
  multiSelect = true,
  fileTypes = ['.ipynb'],
  title = 'Select Files'
}) => {
  const [currentPath, setCurrentPath] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [pathInput, setPathInput] = useState('');
  const [currentItems, setCurrentItems] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [contentsManager, setContentsManager] = useState<ContentsManager | null>(null);

  useEffect(() => {
    const initContentsManager = async () => {
      try {
        const serverSettings = undefined;
        const manager = new ContentsManager({ serverSettings });
        setContentsManager(manager);

        const initialPath = '';
        setCurrentPath(initialPath);
        setPathInput(initialPath);
      } catch (error) {
        console.error('Failed to initialize ContentsManager:', error);
      }
    };

    if (open) {
      initContentsManager();
    }
  }, [open]);

  useEffect(() => {
    const loadDirectoryContents = async () => {
      if (!contentsManager || !open) return;

      setLoading(true);
      try {
        const contents = await contentsManager.get(currentPath, {
          content: true,
          type: 'directory'
        });

        if (contents.type === 'directory' && contents.content) {
          const items: FileItem[] = contents.content.map((item: Contents.IModel) => ({
            id: item.path,
            name: item.name,
            type: item.type === 'directory' ? 'directory' : 'file',
            path: item.path,
            isNotebook: item.type === 'notebook' || item.name.endsWith('.ipynb'),
            size: item.size,
            lastModified: item.last_modified ? new Date(item.last_modified) : undefined
          }));

          const filteredItems = fileTypes.length > 0
            ? items.filter(item =>
              item.type === 'directory' ||
              fileTypes.some(ext => item.name.toLowerCase().endsWith(ext.toLowerCase()))
            )
            : items;

          setCurrentItems(filteredItems);
        }
      } catch (error) {
        console.error('Failed to load directory contents:', error);
        setCurrentItems([]);
      } finally {
        setLoading(false);
      }
    };

    loadDirectoryContents();
  }, [currentPath, contentsManager, open, fileTypes]);

  useEffect(() => setPathInput(currentPath), [currentPath]);

  const getCurrentItems = (): FileItem[] => {
    return currentItems;
  };

  const getSelectedFileItems = (): FileItem[] => {
    return currentItems.filter(item =>
      item.type === 'file' && selectedFiles.has(item.id)
    );
  };

  const handleItemClick = (item: FileItem) => {
    if (item.type === 'directory') {
      setCurrentPath(item.path);
      setSelectedFiles(new Set());
    } else {
      if (multiSelect) {
        const newSelection = new Set(selectedFiles);
        if (newSelection.has(item.id)) {
          newSelection.delete(item.id);
        } else {
          newSelection.add(item.id);
        }
        setSelectedFiles(newSelection);
      } else {
        setSelectedFiles(new Set([item.id]));
      }
    }
  };

  const handleGoUp = () => {
    const pathParts = currentPath.split('/').filter(part => part !== '');
    if (pathParts.length > 0) {
      pathParts.pop();
      const newPath = pathParts.length === 0 ? '' : pathParts.join('/');
      setCurrentPath(newPath);
    }
  };

  const handleGoHome = () => setCurrentPath('');

  const handlePathInputChange = (newPath: string) => setPathInput(newPath);

  const handlePathNavigate = async () => {
    if (!contentsManager) return;

    try {
      const contents = await contentsManager.get(pathInput, { content: false });
      if (contents.type === 'directory') {
        setCurrentPath(pathInput);
      } else {
        setPathInput(currentPath);
      }
    } catch (error) {
      setPathInput(currentPath);
    }
  };

  const handleSelectAll = () => {
    const currentFiles = getCurrentItems().filter(item =>
      item.type === 'file' &&
      (fileTypes.length === 0 || fileTypes.some(ext => item.name.toLowerCase().endsWith(ext.toLowerCase())))
    );
    const newSelection = new Set(selectedFiles);
    currentFiles.forEach(file => newSelection.add(file.id));
    setSelectedFiles(newSelection);
  };

  const handleDeselectAll = () => setSelectedFiles(new Set());

  const handleConfirm = () => {
    const selectedFileItems = getSelectedFileItems();
    if (onFilesSelected) {
      onFilesSelected(selectedFileItems);
    }
    handleCancel();
  };

  const handleCancel = () => { 
    setSelectedFiles(new Set()); 
    onClose(); 
  };

  const selectedFileItems = getSelectedFileItems();
  const isFileSelected = selectedFiles.size > 0;

  return (
    <Dialog
        open={open}
        onClose={handleCancel}
        headerText={title}
        resizable
        draggable
        style={{
          width: '700px',
          height: '520px'
        }}
        className="full-space-dialog"
        footer={
          <div style={{
            padding: '8px 12px',
            borderTop: '1px solid #d9d9d9',
            backgroundColor: '#fafafa',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            minHeight: '40px'
          }}>
            <Text style={{ fontSize: '13px', color: '#6a6a6a' }}>
              {selectedFiles.size} of {currentItems.filter(item => item.type === 'file').length} files selected
            </Text>
            <FlexBox style={{ gap: '8px' }}>
              <Button
                design="Transparent"
                onClick={handleCancel}
                style={{ minWidth: '80px' }}
              >
                Cancel
              </Button>
              <Button
                design="Emphasized"
                onClick={handleConfirm}
                disabled={!isFileSelected}
                style={{ minWidth: '100px' }}
              >
                Select
              </Button>
            </FlexBox>
          </div>
        }
      >
        <style>
          {`.full-space-dialog::part(content) {
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
            height: 100% !important;
          }`}
        </style>
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          <FlexBox
            alignItems={FlexBoxAlignItems.Center}
            style={{
              gap: '6px',
              padding: '6px 12px',
              backgroundColor: '#f7f7f7',
              borderRadius: '0',
              borderBottom: '1px solid #d9d9d9',
              minHeight: '36px'
            }}
          >
            <Button
              icon="navigation-up-arrow"
              design="Transparent"
              onClick={handleGoUp}
              disabled={currentPath === ''}
              tooltip="Parent folder"
              style={{
                width: '28px',
                height: '28px',
                minWidth: '28px',
                padding: '0'
              }}
            />
            <Button
              icon="home"
              design="Transparent"
              onClick={handleGoHome}
              tooltip="Home"
              style={{
                width: '28px',
                height: '28px',
                minWidth: '28px',
                padding: '0'
              }}
            />
            <Input
              value={pathInput}
              onInput={(e: any) => handlePathInputChange(e.target.value)}
              onKeyDown={(e: any) => {
                if (e.key === 'Enter') {
                  handlePathNavigate();
                }
              }}
              style={{
                flex: 1,
                height: '28px',
                fontSize: '13px'
              }}
              placeholder="Path..."
            />
            <Button
              design="Default"
              onClick={handlePathNavigate}
              style={{
                height: '28px',
                minWidth: '40px',
                fontSize: '12px'
              }}
            >
              Go
            </Button>
          </FlexBox>

          <FlexBox
            justifyContent={FlexBoxJustifyContent.SpaceBetween}
            alignItems={FlexBoxAlignItems.Center}
            style={{
              padding: '6px 12px',
              minHeight: '28px',
              backgroundColor: '#fdfdfd',
              borderBottom: '1px solid #eee'
            }}
          >
            <Text style={{
              fontSize: '13px',
              color: '#333',
              fontWeight: '500'
            }}>
              {currentPath || '/'}
            </Text>
            <FlexBox style={{ gap: '4px' }}>
              <Button
                design="Transparent"
                onClick={handleSelectAll}
                tooltip="Select all"
                style={{
                  width: '28px',
                  height: '24px',
                  minWidth: '28px',
                  padding: '0',
                  fontSize: '11px'
                }}
              >
                All
              </Button>
              <Button
                design="Transparent"
                onClick={handleDeselectAll}
                disabled={selectedFiles.size === 0}
                tooltip="Clear selection"
                style={{
                  width: '32px',
                  height: '24px',
                  minWidth: '32px',
                  padding: '0',
                  fontSize: '11px'
                }}
              >
                None
              </Button>
            </FlexBox>
          </FlexBox>

          <div style={{
            flex: 1,
            overflow: 'hidden',
            backgroundColor: 'white'
          }}>
            <div style={{
              height: '100%',
              overflow: 'auto'
            }}>
              {loading ? (
                <div style={{
                  padding: '32px',
                  textAlign: 'center',
                  color: '#999',
                  fontSize: '13px'
                }}>
                  Loading...
                </div>
              ) : currentItems.length === 0 ? (
                <div style={{
                  padding: '32px',
                  textAlign: 'center',
                  color: '#999',
                  fontSize: '13px'
                }}>
                  No files in this directory
                </div>
              ) : (
                currentItems.map((item, index) => {
                  const isSelected = selectedFiles.has(item.id);
                  const isNotebook = item.isNotebook || item.name.endsWith('.ipynb');

                  return (
                    <div
                      key={item.id}
                      onClick={() => handleItemClick(item)}
                      style={{
                        cursor: 'pointer',
                        backgroundColor: isSelected ? '#e8f4fd' : (index % 2 === 0 ? '#fafafa' : 'white'),
                        padding: '4px 12px',
                        borderBottom: index < currentItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                        transition: 'background-color 0.15s ease',
                        minHeight: '28px',
                        display: 'flex',
                        alignItems: 'center'
                      }}
                      onMouseEnter={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.backgroundColor = '#f0f0f0';
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!isSelected) {
                          e.currentTarget.style.backgroundColor = index % 2 === 0 ? '#fafafa' : 'white';
                        }
                      }}
                    >
                      <FlexBox
                        alignItems={FlexBoxAlignItems.Center}
                        justifyContent={FlexBoxJustifyContent.SpaceBetween}
                        style={{ width: '100%' }}
                      >
                        <FlexBox alignItems={FlexBoxAlignItems.Center} style={{ gap: '8px', minWidth: 0 }}>
                          {multiSelect && item.type === 'file' && (
                            <CheckBox
                              checked={isSelected}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleItemClick(item);
                              }}
                              style={{
                                transform: 'scale(0.85)'
                              }}
                            />
                          )}
                          <Icon
                            name={item.type === 'directory' ? 'folder' : 'document'}
                            style={{
                              fontSize: '14px',
                              color: item.type === 'directory' ? '#ff9800' : isNotebook ? '#4caf50' : '#757575',
                              flexShrink: 0
                            }}
                          />
                          <Text style={{
                            fontWeight: item.type === 'directory' ? '500' : '400',
                            fontSize: '13px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}>
                            {item.name}
                          </Text>
                          {isNotebook && (
                            <span style={{
                              backgroundColor: '#e8f5e8',
                              color: '#2e7d32',
                              padding: '1px 4px',
                              borderRadius: '3px',
                              fontSize: '9px',
                              fontWeight: '500',
                              flexShrink: 0
                            }}>
                              .ipynb
                            </span>
                          )}
                        </FlexBox>
                        <Text style={{
                          fontSize: '11px',
                          color: '#999',
                          flexShrink: 0,
                          marginLeft: '8px'
                        }}>
                          {item.type === 'directory' ? 'DIR' : 'FILE'}
                        </Text>
                      </FlexBox>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {selectedFiles.size > 0 && (
            <div style={{
              padding: '6px 12px',
              backgroundColor: '#f8f9fa',
              borderTop: '1px solid #e9ecef',
              maxHeight: '50px',
              overflow: 'hidden'
            }}>
              <Text style={{
                fontSize: '12px',
                fontWeight: '500',
                color: '#495057',
                marginBottom: '4px',
                display: 'block'
              }}>
                Selected ({selectedFiles.size}):
              </Text>
              <div style={{
                fontSize: '11px',
                color: '#6c757d',
                lineHeight: '1.3',
                overflow: 'hidden'
              }}>
                {selectedFileItems.slice(0, 3).map((file, index) => (
                  <span key={file.id}>
                    {index > 0 && ', '}
                    {file.name}
                  </span>
                ))}
                {selectedFileItems.length > 3 && (
                  <span style={{ fontStyle: 'italic' }}>
                    {' '}and {selectedFileItems.length - 3} more...
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </Dialog>
  );
};

export default FilePickerDialog;
