#!/bin/env python3

import pkgbuild
import os
import glob
import graphviz


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


def plot_provides(graph, package_list):
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
                graph.node(p, color='lightblue', style='filled', shape='box')

                for pk in pkg_name:
                    graph.edge(p, pk)


def strip_pkg_name(name):
    name = name.split("<", maxsplit=1)[0]
    name = name.split(">", maxsplit=1)[0]
    name = name.split("=", maxsplit=1)[0]
    return name


def plot_package_dependencies(graph, package_list):
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
                        graph.edge(name, strip_pkg_name(dependency))


def plot_package_makedepends(graph, package_list):
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
                        graph.edge(name, strip_pkg_name(dependency), color='red')


def main():
    root_path = "/home/venom/Sync_ArchPPC/new_arch/packages"
    run_path = os.getcwd()

    path_core = root_path + "/core"
    path_extra = root_path + "/extra"
    path_community = root_path + "/community"

    core_packages = read_pkgbuilds(path_core, "core")
    extra_packages = read_pkgbuilds(path_extra, "extra")
    community_packages = read_pkgbuilds(path_community, "community")

    os.chdir(run_path)

    dot = graphviz.Digraph("PKGBUILD dependency (without makedepends) graph", strict=True)
    plot_package_nodes(dot, core_packages)
    plot_package_nodes(dot, extra_packages)
    plot_package_nodes(dot, community_packages)
    plot_provides(dot, core_packages)
    plot_provides(dot, extra_packages)
    plot_provides(dot, community_packages)
    plot_package_dependencies(dot, core_packages)
    plot_package_dependencies(dot, extra_packages)
    plot_package_dependencies(dot, community_packages)
    dot.render("dep_only")

    dot = graphviz.Digraph("PKGBUILD makedepends graph", strict=True)
    plot_package_nodes(dot, core_packages)
    plot_package_nodes(dot, extra_packages)
    plot_package_nodes(dot, community_packages)
    plot_provides(dot, core_packages)
    plot_provides(dot, extra_packages)
    plot_provides(dot, community_packages)
    plot_package_makedepends(dot, core_packages)
    plot_package_makedepends(dot, extra_packages)
    plot_package_makedepends(dot, community_packages)
    dot.render("makedepends_only")

    dot = graphviz.Digraph("PKGBUILD dependency graph", strict=True)
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
    dot.render("dep_combined")


main()
