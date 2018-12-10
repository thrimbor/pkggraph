#!/bin/env python3

import lzma
import tarfile
import pkgbuild
import os
import glob
# import graphviz
import graph_tool.all as graph_tool


def pkg_to_provideslist(pkgfilepath):
    provideslist = []

    with lzma.open(pkgfilepath) as f:
        with tarfile.open(fileobj=f) as tar:
            with tar.extractfile(".PKGINFO") as fc:
                for l in fc:
                    linestr = l.strip(b'\n').decode("utf-8")
                    linesplit = linestr.split(" = ")
                    if linesplit[0] == "provides":
                        provideslist.append(linesplit[1].split("=")[0])
                    if linesplit[0] == "pkgname":
                        provideslist.append(linesplit[1])

    return provideslist


def get_all_provides(rootpath):
    provideslist = []

    flist = [f for f in glob.iglob(rootpath + "/*/*.pkg.tar.xz", recursive=True)]
    for c, f in enumerate(flist):
        provideslist += pkg_to_provideslist(f)
        print("\rbuilt packages scanned: " + str(c) + "/" + str(len(flist)) + "      ", end='')
    return list(set(provideslist))


def readpkg(pkgbuild_path):
    os.chdir(pkgbuild_path)
    os.system("makepkg --printsrcinfo >/tmp/srcinfo")
    return pkgbuild.SRCINFO("/tmp/srcinfo")


def read_pkgbuilds(path, name):
    packages = []
    flist = [f for f in glob.iglob(path + "/*/PKGBUILD", recursive=True)]
    for c, f in enumerate(flist):
        packages.append(readpkg(os.path.dirname(f)))
        print("\r" + name + ": " + str(c) + "/" + str(len(flist)) + "      ", end='')
    return packages


"""
def plot_package_nodes(graph, package_list):
    for pkg in package_list:
        pkg_name = pkg.content.get("pkgname")
        if isinstance(pkg_name, list):
            with graph.subgraph(name='cluster_' + str(pkg.content.get("pkgbase"))) as split_pkg:
                split_pkg.attr(label=pkg.content.get("pkgbase"))
                split_pkg.attr(style='filled')
                split_pkg.attr(color='lightgrey')
                for name in pkg_name:
                    split_pkg.node(name, color='lightblue', style='filled')
        else:
            graph.node(pkg_name, color='lightblue', style='filled')
"""


def add_or_get_node(graph, all_nodes, nodename, pkgtype='pkg'):
    if not str(nodename) in all_nodes:
        v = graph.add_vertex()
        graph.vertex_properties['pkgname'][v] = str(nodename)
        if pkgtype == 'pkg':
            graph.vertex_properties['vcolor'][v] = 'lightblue'
        elif pkgtype == 'dep' or pkgtype == 'makedep':
            graph.vertex_properties['vcolor'][v] = 'red'
        elif pkgtype == 'provides':
            graph.vertex_properties['vcolor'][v] = 'green'
        all_nodes[str(nodename)] = v
        return v
    else:
        v = all_nodes[str(nodename)]
        if pkgtype == 'pkg':
            graph.vertex_properties['vcolor'][v] = 'lightblue'
        return v


def plot_package_nodes(graph, package_list, all_nodes):
    for pkg in package_list:
        pkg_name = pkg.content.get("pkgname")
        if isinstance(pkg_name, list):
            for name in pkg_name:
                add_or_get_node(graph, all_nodes, name)
                # split_pkg.node(name, color='lightblue', style='filled')
        else:
            add_or_get_node(graph, all_nodes, pkg_name)


def plot_provides(graph, all_nodes, package_list):
    for pkg in package_list:
        pkg_name = pkg.content.get("pkgname")
        if not isinstance(pkg_name, list):
            pkg_name = [pkg_name]

        provides = pkg.content.get("provides")
        if provides:
            if not isinstance(provides, list):
                provides = [provides]
            for p in provides:
                p = strip_pkg_name(p)
                # graph.node(p, color='lightblue', style='filled', shape='box')
                p_node = add_or_get_node(graph, all_nodes, p)

                for pk in pkg_name:
                    pk_node = add_or_get_node(graph, all_nodes, pk, pkgtype='provides')
                    e = graph.add_edge(p_node, pk_node)
                    graph.edge_properties['ecolor'][e] = 'black'
                    # graph.edge(p, pk)


def strip_pkg_name(name):
    name = name.split("<", maxsplit=1)[0]
    name = name.split(">", maxsplit=1)[0]
    name = name.split("=", maxsplit=1)[0]
    return name


def plot_package_dependencies(graph, all_nodes, package_list):
    # FIXME: In split packages, we might have to add pkgbase-dependencies and pkgname-dependencies together
    # FIXME: We're ignoring makedepends
    # FIXME: We're ignoring checkdepends
    for pkg in package_list:
        pkg_name = pkg.content.get("pkgname")
        if not isinstance(pkg_name, list):
            pkg_name = [pkg_name]

        dependencies = pkg.content.get("depends")
        if dependencies:
            if not isinstance(dependencies, list):
                dependencies = [dependencies]
            for dependency in dependencies:
                if len(dependency.strip()) > 0:
                    for name in pkg_name:
                        name_node = add_or_get_node(graph, all_nodes, name, pkgtype='pkg')
                        dep_node = add_or_get_node(graph, all_nodes, strip_pkg_name(dependency), pkgtype='dep')
                        e = graph.add_edge(name_node, dep_node)
                        graph.edge_properties['ecolor'][e] = 'black'
                        # graph.edge(name, strip_pkg_name(dependency))


def plot_package_makedepends(graph, all_nodes, package_list):
    # FIXME: In split packages, we might have to add pkgbase-dependencies and pkgname-dependencies together
    # FIXME: We're ignoring makedepends
    # FIXME: We're ignoring checkdepends
    for pkg in package_list:
        pkg_name = pkg.content.get("pkgname")
        if not isinstance(pkg_name, list):
            pkg_name = [pkg_name]

        dependencies = pkg.content.get("makedepends")
        if dependencies:
            if not isinstance(dependencies, list):
                dependencies = [dependencies]
            for dependency in dependencies:
                if len(dependency.strip()) > 0:
                    for name in pkg_name:
                        name_node = add_or_get_node(graph, all_nodes, name, pkgtype='pkg')
                        dep_node = add_or_get_node(graph, all_nodes, strip_pkg_name(dependency), pkgtype='makedep')
                        e = graph.add_edge(name_node, dep_node)
                        graph.edge_properties['ecolor'][e] = 'red'
                        # graph.edge(name, strip_pkg_name(dependency), color='red')


def main():
    builtpkg_root = "/home/venom/Sync_ArchPPC/new_arch/native_stage1_g5"
    root_path = "/home/venom/Sync_ArchPPC/new_arch/packages"
    run_path = os.getcwd()

    path_core = root_path + "/core"
    path_extra = root_path + "/extra"
    path_community = root_path + "/community"

    core_packages = read_pkgbuilds(path_core, "core")
    extra_packages = read_pkgbuilds(path_extra, "extra")
    community_packages = read_pkgbuilds(path_community, "community")

    os.chdir(run_path)

    provided_packages = get_all_provides(builtpkg_root)

    all_nodes = dict()
    dot = graph_tool.Graph()  # ("PKGBUILD dependency (without makedepends) graph")
    dot.vertex_properties['pkgname'] = dot.new_vertex_property('string')
    dot.vertex_properties['vcolor'] = dot.new_vertex_property('string')
    dot.edge_properties['ecolor'] = dot.new_edge_property('string')
    plot_package_nodes(dot, core_packages, all_nodes)
    plot_package_nodes(dot, extra_packages, all_nodes)
    plot_package_nodes(dot, community_packages, all_nodes)
    plot_provides(dot, all_nodes, core_packages)
    plot_provides(dot, all_nodes, extra_packages)
    plot_provides(dot, all_nodes, community_packages)
    plot_package_dependencies(dot, all_nodes, core_packages)
    plot_package_dependencies(dot, all_nodes, extra_packages)
    plot_package_dependencies(dot, all_nodes, community_packages)
    plot_package_makedepends(dot, all_nodes, core_packages)
    plot_package_makedepends(dot, all_nodes, extra_packages)
    plot_package_makedepends(dot, all_nodes, community_packages)

    # mark all built packages
    for k in all_nodes:
        if k in provided_packages:
            dot.vertex_properties['vcolor'][all_nodes[k]] = '#003ea3'

    pos = graph_tool.arf_layout(dot)
    graph_tool.graph_draw(dot, output_size=(16000, 16000), output="dep_combined.pdf",
                          vertex_text=dot.vertex_properties['pkgname'],
                          vertex_color=dot.vertex_properties['vcolor'],
                          vertex_fill_color=dot.vertex_properties['vcolor'],
                          edge_color=dot.edge_properties['ecolor'],
                          pos=pos)
    # pos = graph_tool.arf_layout(dot)
    # graph_tool.graph_draw(dot, pos=pos, output_size=(16000, 16000), output="dep_combined.pdf",
    #                      vertex_text=dot.vertex_properties['pkgname'])
    return

    dot = graph_tool.Graph()  # ("PKGBUILD makedepends graph", strict=True)
    plot_package_nodes(dot, core_packages)
    plot_package_nodes(dot, extra_packages)
    plot_package_nodes(dot, community_packages)
    plot_provides(dot, core_packages)
    plot_provides(dot, extra_packages)
    plot_provides(dot, community_packages)
    plot_package_makedepends(dot, core_packages)
    plot_package_makedepends(dot, extra_packages)
    plot_package_makedepends(dot, community_packages)
    graph_tool.graph_draw(dot, output="makedepends_only.pdf")

    dot = graph_tool.Graph()  # ("PKGBUILD dependency graph", strict=True)
    plot_package_nodes(dot, core_packages)
    plot_package_nodes(dot, extra_packages)
    plot_package_nodes(dot, community_packages)
    plot_provides(dot, core_packages)
    plot_provides(dot, extra_packages)
    plot_provides(dot, community_packages)
    plot_package_dependencies(dot, core_packages)
    plot_package_dependencies(dot, extra_packages)
    plot_package_dependencies(dot, community_packages)
    plot_package_makedepends(dot, core_packages)
    plot_package_makedepends(dot, extra_packages)
    plot_package_makedepends(dot, community_packages)
    graph_tool.graph_draw(dot, output="dep_combined.pdf")


main()
