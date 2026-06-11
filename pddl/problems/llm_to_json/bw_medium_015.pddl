(define (problem bw_medium_015)
  (:domain blocks-world)

  (:objects
    a b c d - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table c)
    (clear a)
    (clear b)
    (clear d)
    (on d c)
    (handempty)
  )

  (:goal
    (and
      (on a d)
      (on b a)
    )
  )
)
