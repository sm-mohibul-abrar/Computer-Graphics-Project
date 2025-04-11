'''OpenGL extension EXT.geometry_shader4

This module customises the behaviour of the 
OpenGL.raw.GL.EXT.geometry_shader4 to provide a more 
Python-friendly API

Overview (from the spec)
	
	EXT_geometry_shader4 defines a new shader type available to be run on the
	GPU, called a geometry shader. Geometry shaders are run after vertices are
	transformed, but prior to color clamping, flat shading and clipping.
	
	A geometry shader begins with a single primitive (point, line,
	triangle). It can read the attributes of any of the vertices in the
	primitive and use them to generate new primitives. A geometry shader has a
	fixed output primitive type (point, line strip, or triangle strip) and
	emits vertices to define a new primitive. A geometry shader can emit
	multiple disconnected primitives. The primitives emitted by the geometry
	shader are clipped and then processed like an equivalent OpenGL primitive
	specified by the application.
	
	Furthermore, EXT_geometry_shader4 provides four additional primitive
	types: lines with adjacency, line strips with adjacency, separate
	triangles with adjacency, and triangle strips with adjacency.  Some of the
	vertices specified in these new primitive types are not part of the
	ordinary primitives, instead they represent neighboring vertices that are
	adjacent to the two line segment end points (lines/strips) or the three
	triangle edges (triangles/tstrips). These vertices can be accessed by
	geometry shaders and used to match up the vertices emitted by the geometry
	shader with those of neighboring primitives.
	
	Since geometry shaders expect a specific input primitive type, an error
	will occur if the application presents primitives of a different type.
	For example, if a geometry shader expects points, an error will occur at
	Begin() time, if a primitive mode of TRIANGLES is specified.

The official definition of this extension is available here:
http://www.opengl.org/registry/specs/EXT/geometry_shader4.txt
'''
from OpenGL import platform, constant, arrays
from OpenGL import extensions, wrapper
import ctypes
from OpenGL.raw.GL import _types, _glgets
from OpenGL.raw.GL.EXT.geometry_shader4 import *
from OpenGL.raw.GL.EXT.geometry_shader4 import _EXTENSION_NAME

def glInitGeometryShader4EXT():
    '''Return boolean indicating whether this extension is available'''
    from OpenGL import extensions
    return extensions.hasGLExtension( _EXTENSION_NAME )


### END AUTOGENERATED SECTION