import { describe, test, expect } from "vitest";
import {
  getVisibleCourseFolders,
  formatFolderDisplayName,
  VirtualFolderItem,
} from "./virtualFolders";

describe("Virtual Folder Hierarchy and Visibility Seam", () => {
  test("CS340: folders with depth 0 like 'Transformers & Attention Mechanisms' must be visible", () => {
    const cs340Folders: VirtualFolderItem[] = [
      {
        id: "folder-nn-001",
        course_id: "course-cs340",
        name: "Neural Networks & Optimization",
        materialized_path: "/neural-networks",
        depth: 0,
        parent_id: null,
      },
      {
        id: "folder-transformers-002",
        course_id: "course-cs340",
        name: "Transformers & Attention Mechanisms",
        materialized_path: "/transformers",
        depth: 0,
        parent_id: null,
      },
    ];

    const visibleFolders = getVisibleCourseFolders(cs340Folders, "course-cs340");

    // The user must be able to see both folders in CS340 to access Attention_Is_All_You_Need.pdf
    expect(visibleFolders.length).toBe(2);
    expect(
      visibleFolders.some((f) => f.name === "Transformers & Attention Mechanisms")
    ).toBe(true);
    expect(
      visibleFolders.some((f) => f.name === "Neural Networks & Optimization")
    ).toBe(true);

    const transformersFolder = visibleFolders.find(
      (f) => f.name === "Transformers & Attention Mechanisms"
    );
    expect(formatFolderDisplayName(transformersFolder!, "CS340")).toBe(
      "Transformers & Attention Mechanisms"
    );
  });

  test("CS301: preserves both top-level modules (depth 0) and nested subfolders (depth 1)", () => {
    const cs301Folders: VirtualFolderItem[] = [
      {
        id: "folder-consensus",
        course_id: "course-cs301",
        name: "Module 1: Consensus Protocols",
        materialized_path: "/consensus",
        depth: 0,
        parent_id: null,
      },
      {
        id: "folder-raft",
        course_id: "course-cs301",
        name: "Raft & Paxos Formalisms",
        materialized_path: "/consensus/raft-paxos",
        depth: 1,
        parent_id: "folder-consensus",
      },
    ];

    const visibleFolders = getVisibleCourseFolders(cs301Folders, "course-cs301");

    expect(visibleFolders.length).toBe(2);
    expect(
      visibleFolders.some((f) => f.name === "Module 1: Consensus Protocols")
    ).toBe(true);
    expect(
      visibleFolders.some((f) => f.name === "Raft & Paxos Formalisms")
    ).toBe(true);

    // Order check: parent path /consensus must precede child path /consensus/raft-paxos
    expect(visibleFolders[0].materialized_path).toBe("/consensus");
    expect(visibleFolders[1].materialized_path).toBe("/consensus/raft-paxos");
  });

  test("CS101: formats syllabus root folder gracefully without hiding children", () => {
    const cs101Folders: VirtualFolderItem[] = [
      {
        id: "folder-root",
        course_id: "course-cs101",
        name: "CS101",
        materialized_path: "/CS101",
        depth: 0,
        parent_id: null,
      },
      {
        id: "folder-week1",
        course_id: "course-cs101",
        name: "Week_01_Recursion",
        materialized_path: "/CS101/Week_01_Recursion",
        depth: 1,
        parent_id: "folder-root",
      },
    ];

    const visibleFolders = getVisibleCourseFolders(cs101Folders, "course-cs101");
    expect(visibleFolders.length).toBe(2);
    expect(formatFolderDisplayName(visibleFolders[0], "CS101")).toBe(
      "CS101 (Root Module)"
    );
    expect(formatFolderDisplayName(visibleFolders[1], "CS101")).toBe(
      "Week 01 Recursion"
    );
  });
});
