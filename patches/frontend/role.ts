import Vue from 'vue'

declare module 'vue/types/vue' {
  interface Vue {
    $translateRole(role: string, mappings: object): string
  }
}

type RoleMapping = {
  projectAdmin: string
  annotator: string
  annotationApprover: string
  projectManager: string
  undefined: string
}

Vue.prototype.$translateRole = (role: string, mapping: RoleMapping) => {
  if (role === 'project_admin') {
    return mapping.projectAdmin
  } else if (role === 'annotator') {
    return mapping.annotator
  } else if (role === 'annotation_approver') {
    return mapping.annotationApprover
  } else if (role === 'project_manager') {
    return mapping.projectManager
  } else {
    // For any unknown role, just return the role name with formatting
    return role.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }
}

