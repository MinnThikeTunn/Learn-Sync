export interface VirtualFolderItem {
  id: string;
  course_id: string;
  name: string;
  materialized_path: string;
  depth: number;
  parent_id?: string | null;
  document_count?: number;
}

/**
 * Returns all accessible folders for a specific course, ordered hierarchically
 * by materialized_path so parent folders precede child subfolders.
 * Preserves top-level modules (depth 0) such as CS340's Transformers and Neural Networks,
 * as well as nested subfolders (depth >= 1).
 */
export function getVisibleCourseFolders(
  folders: VirtualFolderItem[],
  courseId: string
): VirtualFolderItem[] {
  if (!folders || !courseId) return [];

  const courseFolders = folders.filter((f) => f.course_id === courseId);

  return [...courseFolders].sort((a, b) => {
    const pathA = a.materialized_path || `/${a.name}`;
    const pathB = b.materialized_path || `/${b.name}`;
    return pathA.localeCompare(pathB);
  });
}

/**
 * Formats folder display name cleanly. If a folder's name is identical to the
 * course code at depth 0 (e.g. syllabus parser root container), gives it a friendly
 * 'Course Root' badge.
 */
export function formatFolderDisplayName(
  folder: VirtualFolderItem,
  courseCode?: string
): string {
  if (!folder?.name) return "Folder";
  const rawName = folder.name.replace(/_/g, " ");
  if (
    courseCode &&
    folder.depth === 0 &&
    folder.name.trim().toUpperCase() === courseCode.trim().toUpperCase()
  ) {
    return `${rawName} (Root Module)`;
  }
  return rawName;
}
