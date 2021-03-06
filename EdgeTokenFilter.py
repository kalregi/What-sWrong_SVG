#!/usr/bin/env python3
# -*- coding: utf-8, vim: expandtab:ts=4 -*-

from NLPInstanceFilter import *
from Token import *
from NLPInstance import *

class EdgeTokenFilter(NLPInstanceFilter):

    """
     * Creates a new filter with the given allowed property values.
     *
     * @param allowedProperties A var array of allowed property values. An Edge will be filtered out if none of its tokens
     *                          has a property with an allowed property value (or a property value that contains an
     *                          allowed value, if {@link com.googlecode.whatswrong.EdgeTokenFilter#isWholeWords()} is
     *                          false).
     OR
     * @param allowedPropertyValues A set of allowed property values. An Edge will be filtered out if none of its tokens
     *                              has a property with an allowed property value (or a property value that contains an
     *                              allowed value, if {@link com.googlecode.whatswrong.EdgeTokenFilter#isWholeWords()} is
     *                              false).
    """
    def __init__(self, *allowedProperties):
        """
         * Should we only allow edges that are on the path of tokens that have the allowed properties.
        """
        self._usePath = False

        """
         * If active this property will cause the filter to filter out all tokens for which all edges where filtered out in
         * the edge filtering step.
        """
        self._collaps = False

        """
         * If true at least one edge tokens must contain at least one property value that matches one of the allowed
         * properties. If false it sufficient for the property values to contain an allowed property as substring.
        """
        self._wholeWords = False

        """
         * Set of property values that one of the tokens of an edge has to have so that the edge is not going to be filtered
         * out.
        """
        self._allowedProperties = set()

        self._allowedProperties.update(list(allowedProperties))

    """
     * If active this property will cause the filter to filter out all tokens for which all edges where filtered out in
     * the edge filtering step.
     *
     * @return true if the filter collapses the graph and removes tokens without edge.
    """
    @property
    def collaps(self):
        return self._collaps

    """
     * If active this property will cause the filter to filter out all tokens for which all edges where filtered out in
     * the edge filtering step.
     *
     * @param collaps true if the filter should collapse the graph and remove tokens without edge.
    """
    @collaps.setter
    def collaps(self, value):
        self._collaps = value

    """
     * Usually the filter allows all edges that have tokens with allowed properties. However, if it "uses paths" an edge
     * will only be allowed if it is on a path between two tokens with allowed properties. This also means that if there
     * is only one token with allowed properties all edges will be filtered out.
     *
     * @return true if the filter uses paths."""
    @property
    def usePath(self):
        return self._usePath

    """
     * Sets whether the filter uses paths.
     *
     * @param usePaths should the filter use paths.
     * @see EdgeTokenFilter#isUsePaths()
    """
    @usePath.setter
    def usePath(self, value):
        self._usePath = value

    """
     * Adds an allowed property value. An Edge must have a least one token with at least one property value that either
     * matches one of the allowed property values or contains one of them, depending on {@link
     * EdgeTokenFilter#isWholeWords()}.
     *
     * @param propertyValue the property value to allow.
    """
    def addAllowedProperty(self, propertyValue=str):
        self._allowedProperties.add(propertyValue)

    """
     * Remove an allowed property value.
     *
     * @param propertyValue the property value to remove from the set of allowed property values.
    """
    def removeAllowedProperty(self, propertyValue=str):
        self._allowedProperties.remove(propertyValue)

    """
     * Removes all allowed words. Note that if no allowed words are specified the filter changes it's behaviour and allows
     * all edges.
    """
    def clear(self):
        self._allowedProperties.clear()

    class Path(set):
        def __hash__(self):
            value = 0
            for e in self:
                value += hash(e)
            return value

    """
     * A Paths object is a mapping from token pairs to all paths between the corresponding tokens.
    """
    class Paths():
        def __init__(self):
            self._map = {}

        """
         * Returns the set of paths between the given tokens.
         *
         * @param from the start token.
         * @param to   the end token.
         * @return the set of paths between the tokens.
        """
        def getPaths(self, From=Token, to=Token):
            if From not in self._map:
                return None
            else:
                paths = self._map[From]
                return paths[to]

        """
         * Get all tokens with paths that end in this token and start at the given from token.
         *
         * @param from the token the paths should start at.
         * @return all tokens that have a paths that end in it and start at the provided token.
        """
        def getTos(self, From=Token):
            if From in self._map:
                result = self._map[From]
                return result.keys()
            else:
                return {}

        """
         * Adds a path between the given tokens.
         *
         * @param from the start token.
         * @param to   the end token.
         * @param path the path to add.
        """
        def addPath(self, From=Token, to=Token, path=None):
            if From not in self._map:
                self._map[From] = {}
            paths = self._map[From]
            if to not in paths:
                _set = set()
                paths[to] = _set
            _set = paths[to]
            _set.add(path)

        def __len__(self):
            return len(self._map)

        def keys(self):
            return self._map.keys()


    """
     * Calculates all paths between all tokens of the provided edges.
     *
     * @param edges the edges (graph) to use for getting all paths.
     * @return all paths defined through the provided edges.
    """
    def calculatePaths(self, edges):
        pathsPerLength = []

        paths = EdgeTokenFilter.Paths()
        for edge in edges:
            path = EdgeTokenFilter.Path()
            path.add(edge)
            paths.addPath(edge.From, edge.To, path)
            paths.addPath(edge.To, edge.From, path)
        pathsPerLength.append(paths)
        previous = paths
        first = paths
        while True:
            paths = EdgeTokenFilter.Paths()
            # go over each paths of the previous length and increase their size by one
            for From in previous.keys():
                for over in previous.getTos():
                    for to in first.getTos():
                        for path1 in previous.getPaths(From, over):
                            for path2 in first.getPaths(over, to):
                                if path2 not in path1 and iter(path1).next().getTypePrefix() == iter(path2).next().getTypePrefix():
                                    path = EdgeTokenFilter.Path()
                                    path.update(path1)
                                    path.update(path2)
                                    paths.addPath(From, to, path)
                                    paths.addPath(to, From, path)
            if len(paths) == 0:
                pathsPerLength.append(paths)
            previous = paths
            if len(paths) == 0:
                break
        result = EdgeTokenFilter.Paths()
        for p in pathsPerLength:
            for From in p.keys():
                for to in p.getTos(From):
                    for path in p.getPaths(From, to):
                        result.addPath(From, to, path)
        return result
    """
     * If true at least one edge tokens must contain at least one property value that matches one of the allowed
     * properties. If false it sufficient for the property values to contain an allowed property as substring.
     *
     * @return whether property values need to exactly match the allowed properties or can contain them as a substring.
    """
    @property
    def wholeWords(self):
        return self._wholeWords

    """
     * Sets whether the filter should check for whole word matches of properties.
     *
     * @param wholeWords true iff the filter should check for whold words.
     * @see EdgeTokenFilter#isWholeWords()
    """
    @wholeWords.setter
    def wholeWords(self, value):
        self._wholeWords = value

    """
     * Filters out all edges that do not have at least one token with an allowed property value. If the set of allowed
     * property values is empty this method just returns the original set and does nothing.
     *
     * @param original the input set of edges.
     * @return the filtered out set of edges.
    """
    def filterEdges(self, original):
        if len(self._allowedProperties) == 0:
            return original
        if (self._usePath):
            paths = self.calculatePaths(original)
            result = set()
            for From in paths.keys():
                if From.propertiesContain(substrings=self._allowedProperties, wholeWord=self._wholeWords):
                    for to in paths.getTos(From):
                        if to.propertiesContain(substrings=self._allowedProperties, wholeWord=self._wholeWords):
                            for path in paths.getPaths(From, to):
                                result.update(path)
            return result
        else:
            result = []
            for edge in original:
                if edge.From.propertiesContain(substrings=self._allowedProperties, wholeWord=self._wholeWords) or \
                        edge.To.propertiesContain(substrings=self._allowedProperties, wholeWord=self._wholeWords):
                    result.append(edge)
            return result

    """
     * Returns whether the given value is an allowed property value.
     *
     * @param propertyValue the value to test.
     * @return whether the given value is an allowed property value.
    """
    def allows(self, propertyValue):
        return propertyValue in self._allowedProperties

    """
     * First filters out edges and then filters out tokens without edges if {@link EdgeTokenFilter#isCollaps()} is true.
     *
     * @param original the original nlp instance.
     * @return the filtered instance.
     * @see NLPInstanceFilter#filter(NLPInstance)
    """
    def filter(self, original=NLPInstance):
        edges = self.filterEdges(original.getEdges())
        if not self._collaps:
            return NLPInstance(tokens=original.tokens, edges=edges, renderType=original.renderType,
                               splitPoints=original.splitPoints)
        else:
            tokens =  set()
            for e in edges:
                if e.renderType == Edge.RenderType.dependency:
                    tokens.add(e.From)
                    tokens.add(e.To)
                else:
                    if e.renderType == Edge.RenderType.span:
                        for i in range(e.From.index, e.To.index + 1):
                            tokens.add(original.getToken(index=i))

            _sorted = sorted(tokens, key=attrgetter("int_index"))

            updatedTokens = []
            old2new = {}
            new2old = {}
            for t in _sorted:
                newToken = Token(len(updatedTokens))
                newToken.merge(original.tokens[int(t.index)])
                old2new[t] = newToken
                new2old[newToken] = t
                updatedTokens.append(newToken)

            updatedEdges = set()
            for e in edges:
                updatedEdges.add(Edge(From=old2new[e.From], To=old2new[e.To], label=e.label, note=e.note,
                                      Type=e.type, renderType=e.renderType, description=e.description))
            # find new split points
            splitPoints = []
            newTokenIndex = 0
            for oldSplitPoint in original.splitPoints:
                newToken = updatedTokens[newTokenIndex]
                oldToken = new2old[newToken]
                while newTokenIndex + 1 < len(tokens) and oldToken.index < oldSplitPoint:
                    newTokenIndex += 1
                    newToken = updatedTokens[newTokenIndex]
                    oldToken = new2old[newToken]
                splitPoints.append(newTokenIndex)

            return NLPInstance(tokens=updatedTokens, edges=updatedEdges, renderType=original.renderType,
                               splitPoints=splitPoints)






























